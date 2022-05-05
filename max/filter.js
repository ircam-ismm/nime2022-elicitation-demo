const Max = require('max-api');

const { performance } = require('perf_hooks');

// package imports
var Fili = require('fili');
var SG = require('ml-savitzky-golay').default;
var DTW = require('dynamic-time-warping');


// local imports
var debug = require('./debug.js');
var utils = require('./utils.js');

// utils functions
var timeinterp = new utils.timeinterp();
var unwrap = new utils.unwrap();


var LOGGING_DEBUG = 3;
var LOGGING_DATA = true;
var to_log = {};

////////////////////////////////////////////////////////////////////////////////
// filter from incoming data source
var first_point_state = true;
var fp_timestamp = 0;
var fp_values = [];

Max.addHandler("new_sample", async (...sample) => {
    // Expected format is
    // sample: t, stroke_id, touch, finger_id, _, x, y, p

    var timestamp = parseInt(sample[0]);
    var stroke_id = parseInt(sample[1]);
    var touching = parseInt(sample[2]);
    var finger = parseInt(sample[3]);
    var xyp = sample.slice(-3);

    // we support only touch from finger 1
    if (finger == 1) {

    // detect stroke segmentation
    if (touching && first_point_state) { // first point
        Max.post("FIRST POINT");
        first_point_state = false;
        fp_timestamp = timestamp;
        fp_values = xyp;
    }
    if (!touching) { // last point
        Max.post("LAST POINT");
        if (stroke.length > 10) {
            new_segment(); // send the last recorded data as a new segment
        }
        // reinit global variables
        first_point_state = true;
        for (var i=0; i<NDIMS; i++) {iirFilters[i].reinit();}
        stroke = [];
        speeds = [];
        unwrap.reset();
        var res = await Max.outlet("reset_sg");
        return 0
    }

    // linear time interpolation
    var sample_interp = timeinterp.new_sample(timestamp, xyp, fp_timestamp);
    // loop over interpolated samples
    for (index in sample_interp) {
        var timestamp_interp = sample_interp[index][0];
        var sample_key = timestamp.toString() + "_" + timestamp_interp.toString();
        var xyp_interp = sample_interp[index].slice(-3);
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
var stroke_speed = [];
var stroke_angle = [];
var stroke_dangle = [];

var cur_segment_len = 0;
var last_segment_end = 0;

var SPEED_THRESHOLD = 1.0;
var SG_WINDOW_SIZE = 5;

var sg_options = {
    windowSize: SG_WINDOW_SIZE,
    derivative: 1,
    pad: 'pre',
    padValue: 'replicate',
};


Max.addHandler("segment", async (...sample) => {
    cur_segment_len += 1;
    stroke.push(sample);

    var sample_key = sample[0];
    var xyp = sample.slice(-3);
    var speed = 100*Math.sqrt(Math.pow(xyp[0], 2) + Math.pow(xyp[1], 2));
    stroke_speed.push(speed);
    var angle = Math.atan2(xyp[1], xyp[0]);
    var angle = unwrap.unwrap(angle);
    stroke_angle.push(angle);
    // derivate - two sample late
    var dangle = 0;
    if (stroke.length > SG_WINDOW_SIZE) {
        dangle = SG(stroke_angle.slice(-5), 1, sg_options).slice(-3,-2)[0];
    }
    stroke_dangle.push(dangle);

    Max.post("segment: ", stroke.length, speed);

    // find extrema over the last three recorded points
    if (stroke.length > 3) {
        var last_3 = stroke_speed.slice(-3);
        // local minimum
        if ((last_3[0] > last_3[1]) && (last_3[2] > last_3[1])) {
            Max.post("min: ", stroke.length, last_3[1]);
            if (((last_3[1] < SPEED_THRESHOLD) && (cur_segment_len > 10)) || (cur_segment_len > 50)) {
                Max.post("SEGMENT !!!:", segment_id, stroke.length);
                new_segment();
                last_segment_end = cur_segment_len;
                cur_segment_len = 0;
            }
        }
    }

    if (LOGGING_DATA) {
        var obj = to_log[sample_key];
        if (obj == undefined) {
            obj = {};
        }
        obj['xyp_sg'] = xyp;
        obj['s'] = speed;
        obj['angle'] = angle;
        obj['da'] = dangle;
        obj['segment_id'] = segment_id;
        var res = await Max.outlet("logging_data", JSON.stringify(obj));
    }
});

var segment_id = 0;

async function new_segment() {
    // individual segment within a stroke
    segment_id += 1;
    segment = stroke.slice(last_segment_end, cur_segment_len);
    // compute_features(segment);
}

////////////////////////////////////////////////////////////////////////////////


async function compute_features(segment) {
    // segment : [[t, x, y, p],...]


    // var speed = segment.map(x => 10 * Math.sqrt(Math.pow(x[1], 2) + Math.pow(x[2], 2)));
    // var angle = segment.map(x => Math.atan2(x[2], x[1])); // might need to unwrap
    // var dA = SG(angle, 1, options);
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


