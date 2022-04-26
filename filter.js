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



var LOGGING_DEBUG = 3;
var LOGGING_DATA = true;
var to_log = {};

////////////////////////////////////////////////////////////////////////////////
// filter from incoming data source
var first_point_state = true;
var fp_timestamp = 0;
var fp_values = [];

Max.addHandler("new_sample", async (...sample) => {
    // sample: t, stroke_id, touch, finger_id, _, x, y, p


    var timestamp = parseInt(sample[0]);
    var stroke_id = parseInt(sample[1]);
    var touching = parseInt(sample[2]);
    var finger = parseInt(sample[3]);
    var xyp = sample.slice(-3);

    // we support only touch from finger 1
    if (finger == 1) {

    // detect stroke segmentation
    if (touching && first_point_state) {
        // first point
        Max.post("FIRST POINT");
        first_point_state = false;

        fp_timestamp = timestamp;
        fp_values = xyp;
    }

    // last point
    if (!touching) {
        Max.post("LAST POINT");

        if (stroke.length > 10) {
            new_segment(); // send the last recorded data as a new segment
        }

        first_point_state = true;
        for (var i=0; i<NDIMS; i++) {iirFilters[i].reinit();}
        stroke = [];
        speeds = [];
        timeinterp.reset();
        var res = await Max.outlet("reset_sg");

        return 0
    }

    // linear time interpolation
    var sample_interp = timeinterp.new_sample(timestamp, xyp, fp_timestamp);

    // Max.post("NEW", timestamp, fp_timestamp, touching, finger, first_point_state, sample_interp.length);

    // loop over interpolated samples
    for (index in sample_interp) {
        // if (LOGGING_DEBUG > 1) {Max.post("new_sample", timestamp, sample_interp.length, sample_interp[index][0]);}

        var timestamp_interp = sample_interp[index][0];
        var sample_key = timestamp.toString() + "_" + timestamp_interp.toString();
        var xyp_interp = sample_interp[index].slice(-3);

        // Max.post("NEW", timestamp, timestamp_interp, sample_key);

        // substract current position from first stroke point touchdown
        var rel_xyp = xyp_interp.map(function (num, idx) { return num-fp_values[idx] });
        // lowpass
        var rel_xyp_lp = lowpass(rel_xyp);
        // send to pipo
        var rel_xyp_lp_tosend = rel_xyp_lp.map(function (num, idx) {return num.toFixed(10)});
        var res = [sample_key].concat(rel_xyp_lp_tosend)
        var res = await Max.outlet("lowpass", res.join(" "));

        if (LOGGING_DATA) {
            to_log[sample_key] = {'sample_key': sample_key,
                                  'timestamp0': timestamp,
                                  'timestamp': timestamp_interp,
                                  'stroke_id': stroke_id,
                                  // 'touching': touching,
                                  'xyp': xyp_interp,
                                  'rel_xyp': rel_xyp,
                                  'rel_xyp_lp': rel_xyp_lp,
                                  }
        }
    }
    } // if (finger == 1)
});


////////////////////////////////////////////////////////////////////////////////
// low pass filtering
var iirCalculator = new Fili.CalcCascades();
var availableFilters = iirCalculator.available();
var iirFilterCoeffs = iirCalculator.lowpass({
    order: 3, // cascade 3 biquad filters (max: 12)
    characteristic: 'butterworth',
    Fs: 100, // sampling frequency
    Fc: 10, // cutoff frequency / center frequency for bandpass, bandstop, peak
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
    return filtered
}

////////////////////////////////////////////////////////////////////////////////
// perform SG filtering in pipo and get back results
// receives the derivatives of xyp
var stroke = [];
var speeds = [];
var SPEED_THRESHOLD = 1.0;
Max.addHandler("segment", async (...sample) => {

    // Max.post("IN SEGMENT", sample);

    var sample_key = sample[0];
    var xyp = sample.slice(-3);

    stroke.push(sample);
    var speed = Math.sqrt(Math.pow(xyp[0], 2) + Math.pow(xyp[1], 2));
    speed = 100 * speed;
    speeds.push(speed);

    Max.post("segment: ", stroke.length, speed);


    // Max.post("speed:", speed);
    // find extrema over the last three recorded points
    if (stroke.length > 3) {
        var last_3 = speeds.slice(-3);
        // Max.post("last_3:", last_3, last_3[0] > last_3[1], last_3[2] > last_3[1]);
        // local minimum
        if ((last_3[0] > last_3[1]) && (last_3[2] > last_3[1])) {
            Max.post("min: ", stroke.length, last_3[1]);
            if ((last_3[1] < SPEED_THRESHOLD) || (stroke.length > 50)) {
                Max.post("SEGMENT !!!:", segment_id, stroke.length);
                new_segment();
            }
        }
    }

    if (LOGGING_DATA) {
        // Max.post("SEGMENT", sample_key);
        var obj = to_log[sample_key];
        if (obj == undefined) {
            obj = {};
        }
        obj['xyp_sg'] = xyp;
        var res = await Max.outlet("logging_data", JSON.stringify(obj));
    }

});

var segment_id = 0;

async function new_segment() {
    // individual segment within a stroke
    segment_id += 1;
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


    var speed = segment.map(x => 10 * Math.sqrt(Math.pow(x[1], 2) + Math.pow(x[2], 2)));
    var angle = segment.map(x => Math.atan2(x[2], x[1])); // might need to unwrap
    var dA = SG(angle, 1, options);
    // ADD pressure!!
    // concat
    var features = speed.map(function(num, idx) {return [num, dA[idx]]})

    var res = [-1, -1];
    if (segment.length > 10) {
        var startTime = performance.now();
        var res = compute_distance(features);
        var endTime = performance.now();
        Max.post("DTW", res, endTime - startTime);
        var dtw = await Max.outlet("dtw", res[1]);
    }

    if (LOGGING_DATA) {
        for (var i = 0; i < features.length; i++) {
            var obj = {'sample_key': segment[i][0],
                       's': features[i][0],
                       'da': features[i][1],
                       'segment_id': segment_id,
                       'min_dtw': res[1],
                       'min_dtw_id': res[0],
                      };
            var tmp = await Max.outlet("logging_feat", JSON.stringify(obj));
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
    // Computes the minimum DTW distance of A against all previously recorded
    // identified segments.
    // Inputs:
    //   A: a multidimensional equispaced time series.
    // Returns:
    //   The minimum DTW distance.

    var min_key = 0;
    var min_dist = 10000;

    n_models = Object.keys(models).length;
    // if no models yet, store series and return
    if (n_models == 0) {
        models[0] = A;
    }
    // else loop over all models and find closest
    else {

        for (key in models) {
            var B = models[key];
            var dtw = new DTW(A, B, distance_p1_2d);
            var cur_dist = dtw.getDistance();

            if (cur_dist < min_dist) {
                min_key = key;
                min_dist = cur_dist;
            }
        }
        // store model
        models[n_models] = A;
    }

    return [min_key, min_dist]
}

////////////////////////////////////////////////////////////////////////////////
// TRASH
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Max.addHandler("new_state", async (...state) => {
//     Max.post("new_state:", state);
//     // new state is one one touch down and 0 on touch up
//     new_stroke = (state == 1);
//     if (new_stroke) {
//         Max.post("new stroke\n");

//     }
//     else {
//         // reset LPF and SG
//         for (var i=0; i<NDIMS; i++) {
//             iirFilters[i].reinit();
//         }
//         var res = await Max.outlet("reset_sg");
//         // erase stored data
//         stroke = [];
//         speeds = [];
//         timeinterp.reset();
//         Max.post("end stroke\n");
//     }
// });


    //     if (first_point_state) {
    //         if (LOGGING_DEBUG > 0) {Max.post("stroke touchdown", timestamp_interp, xyp_interp);}
    //         first_point_value = xyp_interp;
    //         first_point_value[2] = 0; // initial pressure is always 0
    //         first_point_state = false;
    //     }

    // substract current position from first stroke point touchdown
    //     var finger = sample[1];
    //     if (finger == 1) {
    //         var rel_xyp = xyp_interp.map(function (num, idx) { return num-first_point_value[idx] });
    //         var rel_xyp_lp = lowpass(rel_xyp);

    //         // send to pipo
    //         rel_xyp_lp = rel_xyp_lp.map(function (num, idx) {return num.toFixed(10)});
    //         var res = [timestamp_interp].concat(rel_xyp_lp)
    //         var res = await Max.outlet("lowpass", res.join(" "));

    //         if (LOGGING_DATA) {
    //             var obj = to_log[timestamp_interp]
    //             obj['xyp_lp'] = rel_xyp_lp;
    //         }
    //     }
    // }