const Max = require('max-api');

// package imports
var Fili = require('fili');
var SG = require('ml-savitzky-golay').default;
var DTW = require("dynamic-time-warping")

// local imports
var debug = require('./debug.js');

var LOGGING = true;
var to_log = {};
var N_STROKE = 0;

////////////////////////////////////////////////////////////////////////////////
// 1. handle state, relative position
// 2. resample uniformly in time
// 3. low pass
var new_stroke = false;
var first_point = [];

Max.addHandler("new_sample", async (...sample) => {
    // Max.post("new_sample: ", sample);

    timestamp = sample[0];
    xyp = sample.slice(-3);

    // LOGGING
    if (LOGGING) {
        to_log[timestamp] = {'xyp': xyp, 'new_stroke': new_stroke};
    }

    if (new_stroke) {
        Max.post("stroke touchdown", xyp);
        first_point = xyp;
        first_point[2] = 0; // initial pressure is always 0
        new_stroke = false;
    }

    // substract current position from first stroke point touchdown
    var finger = sample[1];
    if (finger == 1) {
        var rel_xyp = xyp.map(function (num, idx) { return num-first_point[idx] });
        var rel_xyp_lp = lowpass(rel_xyp);

        // send to pipo

        var res = [timestamp].concat(rel_xyp_lp)
        var res = res.map(function (num, idx) {return num.toFixed(20)});
        // Max.post(timestamp, rel_xyp_lp);
        var res = await Max.outlet("lowpass", res.join(" "));

        // LOGGING
        if (LOGGING) {
            var obj = to_log[timestamp]
            obj['xyp_lp'] = rel_xyp_lp;
        }
    }

});

Max.addHandler("new_state", async (...state) => {
    Max.post("new_state: ", state);

    new_stroke = (state == 1);
    if (new_stroke) {
        Max.post("new stroke\n");

        fun_new_stroke();
        erase_last_stroke();
    }
    else {
        Max.post("end stroke\n");

        var res = compute_features(stroke);
        // post("end stroke\n");
        // outlet(1, "end_stroke");
    }

});



async function fun_new_stroke(arg) {
// reset LPF
    reset_filters();
// reset SG
    var res = await Max.outlet("reset_sg");
}

function reset_filters(arg) {
    for (var i=0; i<NDIMS; i++) {
        iirFilters[i].reinit();
    }
}

////////////////////////////////////////////////////////////////////////////////
// Instance of a filter coefficient calculator, get available filters
// calculate filter coefficients
var iirCalculator = new Fili.CalcCascades();
var availableFilters = iirCalculator.available();
var iirFilterCoeffs = iirCalculator.lowpass({
    order: 3, // cascade 3 biquad filters (max: 12)
    characteristic: 'butterworth',
    Fs: 100, // sampling frequency
    Fc: 10, // cutoff frequency / center frequency for bandpass, bandstop, peak
    // BW: 1, // bandwidth only for bandstop and bandpass filters - optional
    // gain: 0, // gain for peak, lowshelf and highshelf
    // preGain: false // adds one constant multiplication for highpass and lowpass
    // k = (1 + cos(omega)) * 0.5 / k = 1 with preGain == false
  });
//create a filter instance from the calculated coeffs
var NDIMS = 3;
var iirFilters = []
for (var i=0; i<NDIMS; i++) {
    iirFilters[i] = new Fili.IirFilter(iirFilterCoeffs);
}

function lowpass(sample) {
    var filtered = [];
    for (var i=0; i<NDIMS; i++) {
        filtered[i] = iirFilters[i].singleStep(sample[i])
    }
    // var res = await Max.outlet("lowpass", JSON.stringify(filtered));
    return filtered
}

////////////////////////////////////////////////////////////////////////////////
// 4. SG
// this is done in PIPO

////////////////////////////////////////////////////////////////////////////////
// 5. segment

var stroke = [];
var speeds = [];
var SPEED_THRESHOLD = 1.0;
Max.addHandler("segment", async (...sample) => {
    // Max.post("segment: ", sample);
    var timestamp = sample[0];
    var xyp = sample.slice(-3);

    if (LOGGING) {
        var obj = to_log[timestamp];
        obj['xyp_sg'] = xyp;
        obj['timestamp'] = timestamp;
        obj['n_stroke'] = N_STROKE;
        var res = await Max.outlet("logging", JSON.stringify(obj));
    }

    stroke.push(xyp);

    var speed = Math.pow(xyp[0], 2) + Math.pow(xyp[1], 2);
    speed = 10000 * speed;
    speeds.push(speed);

    Max.post("speed:", speed);

    // find extrema over the last three recorded points
    if (stroke.length > 3) {
        var last_3 = speeds.slice(-3);
        // Max.post("last_3:", last_3, last_3[0] > last_3[1], last_3[2] > last_3[1]);

        // local minimum
        if ((last_3[0] > last_3[1]) && (last_3[2] > last_3[1])) {
            Max.post("min: ", stroke.length, last_3[0], last_3[1], last_3[2]);
            if ((last_3[1] < SPEED_THRESHOLD) || (stroke.length > 50)) {
                new_segment();
            }
        }
    }

});

async function new_segment() {
// individual segment within a stroke
    N_STROKE += 1;

    Max.post("SEGMENT:", N_STROKE, stroke.length);
    segment = stroke.splice(0, stroke.length-1);
    compute_features(segment);
    // if (LOGGING) {
    //     to_log['N_STROKE'] = N_STROKE;
    //     var res = await Max.outlet("logging", JSON.stringify(to_log));
    //     Max.post("SEND RES !!!", res);
    // }
    // to_log = {};
}

function erase_last_stroke() {
// new touch detected
    stroke = [];
    speeds = []
}

// function end_stroke() {
// // end of touch detected
//     outlet(0, stroke.join(" "));
// }


////////////////////////////////////////////////////////////////////////////////
// 5. features


var options = {
    derivative: 1,
    pad: 'post',
    padValue: 'replicate',
};
// compute features
// python code is:
// sample['s'] = np.linalg.norm(sample[['x1', 'y1']], axis=1)
// alpha = np.arctan2(sample['y1'], sample['x1'])
// sample['a'] = np.unwrap(alpha, period=np.pi)
// sample['da'] = scsig.savgol_filter(sample['a'], deriv=1, **savgol_dict) * 10
async function compute_features(segment) {
    // segment = segment[0].split(" ");
    // segment = segment.map(x => JSON.parse("[" + x + "]"));

    if (segment.length > 10) {
        speed = segment.map(x => Math.pow(x[0], 2) + Math.pow(x[1], 2));
        angle = segment.map(x => Math.atan2(x[1], x[0]));
        var dA = SG(angle, 1, options);

        // Max.post(angle);
        // Max.post(dA); // first derivative
        Max.post(speed.length, angle.length);
    }
}





// Max.addHandler("lowpass", async (...sample) => {
//     // debug_print("lowpass", sample);
//     var filtered = [];
//     for (var i=0; i<NDIMS; i++) {
//         filtered[i] = iirFilters[i].singleStep(sample[i])
//     }
//     // var res = await Max.outlet("lowpass", JSON.stringify(filtered));
//     filtered = filtered.map(function (num, idx) {return num.toFixed(9)});
//     // var res = await Max.outlet("lowpass", filtered.join(" "));
// });


// Max.addHandler("new_stroke", async (unused) => {
//     Max.post("node = : new_stroke");
//     // reset filters
//     for (var i=0; i<NDIMS; i++) {
//         iirFilters[i].reinit();
//     }
// });

// Max.addHandler("end_stroke", async (unused) => {
// });


// Max.addHandler("stroke", async (unused) => {

// });

// // var dtw = new DTW(A, B, fun);
// // var dist = dtw.getDistance();
// // console.log(dist);

// var fun = function (a, b) {
//     var diff = a.map(function (i,j) {return Math.abs(i - b[j])});
//     var sum = diff.reduce((a, b) => a + b, 0);
//     return sum
// }

// function unravel(X) {
//     return X;
// }
