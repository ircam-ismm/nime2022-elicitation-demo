const Max = require('max-api');

const { performance } = require('perf_hooks');
var cluster = require('cluster');

// package imports
const nj = require('numjs');
var SG = require('ml-savitzky-golay').default;
var computeHistogram = require( 'compute-histogram' );

// local imports
var utils = require('./utils.js');
var dtw_worker = require('./distance_model.js');

// logging
var LOGGING_DATA = 2; // 1: output to max, 2: write to log file
var to_log = {};
var logger = LOGGING_DATA == 2  ?  new utils.Logger()  :  undefined;

////////////////////////////////////////////////////////////////////////////////
// DTW callback
// https://math.stackexchange.com/questions/106700/incremental-averaging
var avg_dtw = 0;
var n_dtw = 1;

dtw_worker.addListener(async function(res) {

    var min_dtw = res['min_dtw_pond'];
    avg_dtw = avg_dtw + (min_dtw - avg_dtw) / n_dtw;
    n_dtw += 1;
    res['avg_dtw'] = avg_dtw;
    res['dtw']     = min_dtw / avg_dtw;
    res['logtype'] = 'segment';

    if (LOGGING_DATA == 1) {
        var out = await Max.outlet('logging_dtw', JSON.stringify(res));
    }
    else if (LOGGING_DATA == 2) {
        logger.log(res);
    }

    var out = await Max.outlet('dtw', min_dtw);
    Max.post('cb', (min_dtw/avg_dtw).toFixed(2), min_dtw.toFixed(2), avg_dtw.toFixed(2));
});



////////////////////////////////////////////////////////////////////////////////
// filter from incoming data source and send to pipo savgol
var first_point_state = true;
var fp_timestamp = 0;
var fp_values = [];

var lowpass = new utils.Lowpass();
var timeinterp = new utils.TimeInterpolation();
var unwrap = new utils.Unwrap();
var debug = new utils.Debug();

var stroke = [];
var stroke_speed = [];
var stroke_angle = [];
var stroke_dangle = [];
var stroke_pressure = [];
var stroke_x = [];
var stroke_y = [];

var cur_segment_len = 0;
var last_segment_end = 0;
var current_input = [ -1, 'unknown' ];
var current_feedback = [ -1, -1, -1, -1, -1 ]; // dsp on, novelty on, synth on, novelty dB, synth dB

var SPEED_THRESHOLD = 1.0;
var SG_WINDOW_SIZE = 5;

var sg_options = {
    windowSize: SG_WINDOW_SIZE,
    derivative: 1,
    pad: 'pre',
    padValue: 'replicate',
};

Max.addHandler('current_input', async (...index) => {
    current_input = [ parseInt(index[0]), index[1] ];
});


// dsp on, novelty on, synth on, novelty dB, synth dB
Max.addHandler('current_feedback', async (...values) => {
    Max.post("UPDATE FEEDBACK CONDITION");
    current_feedback = [ ...values ];
});

	
// log events: timetag, symbols...
Max.addHandler('log_event', async (...values) => {
    res = { 'logtype': 'event', 'timestamp0': parseInt(values[0]), 'event': values.slice(1) };

    if (LOGGING_DATA == 1) {
        var out = await Max.outlet('logging_event', JSON.stringify(res));
    }
    else if (LOGGING_DATA == 2) {
        logger.log(res);
    }
});

Max.addHandler('new_sample', async (...sample) => {
    // Expected format is
    // sample: t, stroke_id, touch, finger_id, _, x, y, p

    var timestamp = parseInt(sample[0]);
    var stroke_id = parseInt(sample[1]);
    var touching = parseInt(sample[2]);
    var finger = parseInt(sample[3]);
    var xyp = sample.slice(-3);

    // we support only touch from finger 1
    if (finger == 1) {

        // stroke segmentation
        if (touching && first_point_state) { // first point
            Max.post('FIRST POINT');
            first_point_state = false;
            fp_timestamp = timestamp;
            fp_values = xyp;
        }
        if (!touching) { // last point
            Max.post('LAST POINT');
            if (cur_segment_len > 10) {
                new_segment(cur_segment_len); // send the last recorded data as a new segment
            }
            // reinit global variables
            first_point_state = true;

            stroke = [];
            stroke_speed = [];
            stroke_angle = [];
            stroke_pressure = [];
            stroke_dangle = [];
            stroke_x = [];
            stroke_y = [];

            unwrap.reset();
            lowpass.reset();
            // var res = await Max.outlet('reset_sg');
            return 0
        }

        // linear time interpolation
        var sample_interp = timeinterp.new_sample(timestamp, xyp, fp_timestamp);
        // loop over interpolated samples

        for (index in sample_interp) {

            cur_segment_len += 1;

            var timestamp_interp = sample_interp[index][0];
            var sample_key = timestamp.toString() + '_' + timestamp_interp.toString();

            var xyp_interp = sample_interp[index].slice(-3);
            // substract current position from first stroke point touchdown
            var rel_xyp = xyp_interp.map(function (num, idx) { return num-fp_values[idx] });
            // lowpass
            var rel_xyp_lp = lowpass.lowpass(rel_xyp);
            stroke.push(rel_xyp_lp);
            stroke_pressure.push(10*rel_xyp_lp[2]);

            // derivate x,y
            var x = rel_xyp_lp[0];
            var y = rel_xyp_lp[1];
            stroke_x.push(x);
            stroke_y.push(y);
            var dx, dy;
            if (stroke.length > SG_WINDOW_SIZE) {
                dx = SG(stroke_x.slice(-5), 1, sg_options).slice(-3,-2)[0];
                dy = SG(stroke_y.slice(-5), 1, sg_options).slice(-3,-2)[0];
            }
            else {
                dx = 0;
                dy = 0;
            }

            // compute speed
            var speed = 100*Math.sqrt(Math.pow(dx, 2) + Math.pow(dy, 2));
            stroke_speed.push(speed);
            // compute angle and unwrap
            var angle = Math.atan2(dy, dx);
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

                    if (((last_3[1] < SPEED_THRESHOLD) && (cur_segment_len > 10)) || (cur_segment_len > 120)) {
                        Max.post('SEGMENT:', segment_id, stroke.length);
                        new_segment(cur_segment_len);
                        last_segment_end = cur_segment_len;
                        cur_segment_len = 0;
                    }
                }
            }

            if (LOGGING_DATA > 0) {
                to_log = {
		    'logtype': 'data',		    
                    'sample_key': sample_key,
                    'timestamp0': timestamp,
                    'timestamp': timestamp_interp,
                    'stroke_id': stroke_id,
                    'segment_id': segment_id,
                    // 'xyp': xyp_interp,
                    'x': xyp_interp[0],
                    'y': xyp_interp[1],
                    'p': xyp_interp[2],
                    // 'rel_xyp': rel_xyp,
                    'x_': rel_xyp[0],
                    'y_': rel_xyp[1],
                    'p_': rel_xyp[2],
                    // 'rel_xyp_lp': rel_xyp_lp,
                    'x0': rel_xyp_lp[0],
                    'y0': rel_xyp_lp[1],
                    'p0': rel_xyp_lp[2],
                    // 'dx_dy': [dx, dy],
                    'x1': dx,
                    'y1': dy,
                    // features
                    's': speed,
                    'angle': angle,
                    'dangle': dangle,
                    'input': current_input,
                    'audio': current_feedback,
                }

                if (LOGGING_DATA == 1) {
                    var res = await Max.outlet('logging_data', JSON.stringify(to_log));
                }
                else if (LOGGING_DATA == 2) {
                    logger.log(to_log);
                }
                to_log = {};
            } // if logging
        } // for each sample
    } // if (finger == 1)
});


const average = (array) => array.reduce((a, b) => a + b) / array.length;


var segment_id = 0;
function new_segment(cur_segment_len) {

    var speed = stroke_speed.slice(-cur_segment_len);
    var dangle = stroke_dangle.slice(-cur_segment_len);
    var pressure = stroke_pressure.slice(-cur_segment_len);

    var features = speed.map(function(num, idx) {return [num, dangle[idx], pressure[idx]]})

    // filter segments smaller than 10 samples, and those with low average speed (stationnary touch)
    if (features.length > 10) {
        var avg = average(speed);
        if (avg > 0.01) {
            var startTime = performance.now();
            dtw_worker.processDtw({'msg':'test', 'now': startTime, 'segment_id':segment_id, 'features': features});
        }
    }
    segment_id += 1;
}

