const Max = require('max-api');

const { performance } = require('perf_hooks');

// package imports
var Fili = require('fili');
var SG = require('ml-savitzky-golay').default;
var DTW = require("dynamic-time-warping");
var nj = require("numjs");

// local imports
var debug = require('./debug.js');
var timeinterp = require('./timeinterp.js');

var LOGGING_DEBUG = 1;
var LOGGING_DATA = true;
var to_log = {};
var N_STROKE = 0;

////////////////////////////////////////////////////////////////////////////////
var new_stroke = false;
var first_point = [];

Max.addHandler("new_sample", async (...sample) => {
    // sample: t, ..., x, y, p

    // linear time interpolation
    var timestamp0 = parseInt(sample[0]);
    var xyp = sample.slice(-3);
    var sample_interp = timeinterp.new_sample(timestamp0, xyp);

    Max.post("res", sample, sample_interp.length);

    // loop over interpolated samples
    for (index in sample_interp) {
        if (LOGGING_DEBUG > 1) {Max.post(timestamp0, sample_interp.length, sample_interp[index][0]);}

        var timestamp_interp = sample_interp[index][0];
        var xyp_interp = sample_interp[index].slice(-3);

        if (LOGGING_DATA) {
            to_log[timestamp_interp] = {'xyp': xyp_interp, 'new_stroke': new_stroke};
        }

        if (new_stroke) {
            if (LOGGING_DEBUG > 0) {Max.post("stroke touchdown", timestamp_interp, xyp_interp);}
            first_point = xyp_interp;
            first_point[2] = 0; // initial pressure is always 0
            new_stroke = false;
        }

        // substract current position from first stroke point touchdown
        var finger = sample[1];
        if (finger == 1) {
            var rel_xyp = xyp_interp.map(function (num, idx) { return num-first_point[idx] });
            var rel_xyp_lp = lowpass(rel_xyp);

            // send to pipo
            rel_xyp_lp = rel_xyp_lp.map(function (num, idx) {return num.toFixed(10)});
            var res = [timestamp_interp].concat(rel_xyp_lp)
            var res = await Max.outlet("lowpass", res.join(" "));

            if (LOGGING_DATA) {
                var obj = to_log[timestamp_interp]
                obj['xyp_lp'] = rel_xyp_lp;
            }
        }
    }

});

////////////////////////////////////////////////////////////////////////////////
Max.addHandler("new_state", async (...state) => {
    Max.post("new_state:", state);
    // new state is one one touch down and 0 on touch up
    new_stroke = (state == 1);
    if (new_stroke) {
        Max.post("new stroke\n");

    }
    else {
        // reset LPF and SG
        for (var i=0; i<NDIMS; i++) {
            iirFilters[i].reinit();
        }
        var res = await Max.outlet("reset_sg");
        // erase stored data
        stroke = [];
        speeds = [];
        timeinterp.reset();
        Max.post("end stroke\n");
    }
});

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
    // Max.post("segment", sample); //, timestamp, xyp, to_log);

    // sample = sample.split(" ");
    // Max.post("segment: ", sample);
    var timestamp = sample[0];
    var xyp = sample.slice(-3);

    if (LOGGING_DATA) {
        var obj = to_log[timestamp];
        obj['xyp_sg'] = xyp;
        obj['timestamp'] = timestamp;
        obj['n_stroke'] = N_STROKE;
        var res = await Max.outlet("logging_data", JSON.stringify(obj));
    }

    stroke.push(sample);

    var speed = Math.pow(xyp[0], 2) + Math.pow(xyp[1], 2);
    speed = 10000 * speed;
    speeds.push(speed);

    // Max.post("speed:", speed);

    // find extrema over the last three recorded points
    if (stroke.length > 3) {
        var last_3 = speeds.slice(-3);
        // Max.post("last_3:", last_3, last_3[0] > last_3[1], last_3[2] > last_3[1]);

        // local minimum
        if ((last_3[0] > last_3[1]) && (last_3[2] > last_3[1])) {
            // Max.post("min: ", stroke.length, last_3[0], last_3[1], last_3[2]);
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
}

////////////////////////////////////////////////////////////////////////////////
var options = {
    derivative: 1,
    pad: 'post',
    padValue: 'replicate',
};

async function compute_features(segment) {
    // segment : [[t, x, y, p],...]

    if (segment.length > 10) {
        var speed = segment.map(x => Math.pow(x[1], 2) + Math.pow(x[2], 2));
        var angle = segment.map(x => Math.atan2(x[2], x[1])); // might need to unwrap
        var dA = SG(angle, 1, options);

        // concat
        var features = speed.map(function(num, idx) {return [num, dA[idx]]})

        var startTime = performance.now();
        var res = compute_distance(features);
        var endTime = performance.now();

        Max.post("DTW", res, endTime - startTime);
        var dtw = await Max.outlet("dtw", res[1]);

        if (LOGGING_DATA) {
            var res = features.map(function(num, idx) {
                return [num[0], num[1], N_STROKE, segment[idx][0], res[0], res[1]]
            });
            for (var i = 0; i < res.length; i++) {
                // Max.post("feat", res[i]);
                var tmp = await Max.outlet("logging_feat", JSON.stringify(res[i]));
            }
            // res = await Max.outlet("logging_feat", JSON.stringify(res));
        }
    }
}


var distance_p1_2d = function (a, b) {
    var diff = a.map(function (i,j) {return Math.abs(i - b[j])});
    var sum = diff.reduce((a, b) => a + b, 0);
    return sum
}


var models = {};
function compute_distance(A) {
    n_models = Object.keys(models).length;
    if (n_models == 0) {
        models[0] = A;
    }
    else {
        var min_key = 0;
        var min_dist = 10000;
        for (key in models) {
            var B = models[key];
            var cur_dist = new DTW(A, B, distance_p1_2d);
            var dist = cur_dist.getDistance();

            if (dist < min_dist) {
                min_key = key;
                min_dist = dist;
            }
            // store model
            models[n_models] = A;
        }
    }
    return [min_key, min_dist]
}

