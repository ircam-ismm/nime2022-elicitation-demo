const Max = require('max-api');

const { performance } = require('perf_hooks');
var cluster = require('cluster');

// package imports
const nj = require('numjs');
var SG = require('ml-savitzky-golay').default;
var computeHistogram = require( 'compute-histogram' );

// local imports
var utils = require('./utils.js');
var dtw_worker = require('./distance_model.js')

// logging
var LOGGING_DATA = true;
var to_log = {};


////////////////////////////////////////////////////////////////////////////////
// DTW callback

var DTW_HIST_FREQ = 10;
var dtw_values = [];

dtw_worker.addListener(async function(res) {
    Max.post("cb", res);
    var out = await Max.outlet("logging_dtw", JSON.stringify(res));

    var feedback = 0;
    if (res['segment_id'] == res['best_id']) {
        feedback = 10;
    }

    dtw_values.push(res['min_dtw']);

    var out = await Max.outlet("dtw", res['min_dtw_pond']);
});


////////////////////////////////////////////////////////////////////////////////
// filter from incoming data source and send to pipo savgol
var first_point_state = true;
var fp_timestamp = 0;
var fp_values = [];

var lowpass = new utils.Lowpass();
var timeinterp = new utils.TimeInterpolation();
var unwrap = new utils.Unwrap();

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

        stroke = [];
        stroke_speed = [];
        stroke_angle = [];
        stroke_dangle = [];

        unwrap.reset();
        lowpass.reset();
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
        var rel_xyp_lp = lowpass.lowpass(rel_xyp);
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
// receives the derivatives of xyp
var stroke = [];
var stroke_speed = [];
var stroke_angle = [];
var stroke_dangle = [];

var cur_segment_len = 0;
var last_segment_end = 0;

var SPEED_THRESHOLD = 0.5;
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

    // find extrema over the last three recorded points
    if (stroke.length > 3) {
        var last_3 = stroke_speed.slice(-3);

        // local minimum
        if ((last_3[0] > last_3[1]) && (last_3[2] > last_3[1])) {

            // Max.post("min: ", stroke.length, last_3[1]);
            if (((last_3[1] < SPEED_THRESHOLD) && (cur_segment_len > 20)) || (cur_segment_len > 120)) {
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

    var speed = stroke_speed.slice(-cur_segment_len);
    var dangle = stroke_dangle.slice(-cur_segment_len);
    var features = speed.map(function(num, idx) {return [num, dangle[idx]]})

    if (features.length > 10) {
        var startTime = performance.now();
        dtw_worker.processDtw({'msg':'test', 'now': startTime, 'segment_id':segment_id, 'features': features});
    }
    segment_id += 1;
}


