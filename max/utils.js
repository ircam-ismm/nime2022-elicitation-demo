const Max = require('max-api');
const nj = require('numjs');
var Fili = require('fili');
var DTW = require('dynamic-time-warping');

var Linear = require('everpolate').linear

////////////////////////////////////////////////////////////////////////////////
// TIME INTERPOLATION
function ti_obj() {

    this.stepsize = 10;
    this.last_timestamp = 0;
    this.last_values = [];

    this.new_sample = function(timestamp, values, fp_timestamp) {
        // Linear interpolation of incomming stream
        // Inputs:
        //   timestamp: sampling time of current sample.
        //   values: array containing independent dimensions to filter.
        //   fp_timestamp: sampling time of original sample, all subsequent
        //               sample of zeroed in time against it.
        // Returns:
        //   An 2D array with rows containing the new sampling time and associated
        //   filtered values.

        if (timestamp == fp_timestamp) {
            this.last_timestamp = 0;
            this.last_values = values;
            return [[0].concat(values)]
        }
        // else
        timestamp = timestamp-fp_timestamp;
        starttime = this.last_timestamp + (this.stepsize - this.last_timestamp) % this.stepsize;
        endtime = timestamp;

        // fix for timestamp that happen on this.stepsize:
        // consequence of last line: res.slice(1)
        if ((endtime%this.stepsize)==0){endtime += 1;}

        time_steps = nj.arange(starttime, endtime, this.stepsize);
        value_steps = values.map(function (element, index) {
            return Linear(time_steps.tolist(), [this.last_timestamp, timestamp], [this.last_values[index], element])},
            this); //need to pass this to map
        value_steps = nj.array(value_steps).T.tolist();
        this.last_timestamp = timestamp
        this.last_values = values

        var res = time_steps.tolist().map(function (element, index) {
            return [element].concat(value_steps[index])
        })

        return res.slice(1)
    }
}

////////////////////////////////////////////////////////////////////////////////
// LOW PASS FILTERING
function lowpass() {
    this.iirCalculator = new Fili.CalcCascades();
    this.availableFilters = this.iirCalculator.available();
    this.iirFilterCoeffs = this.iirCalculator.lowpass({
        order: 3, // cascade 3 biquad filters (max: 12)
        characteristic: 'butterworth',
        Fs: 100, // sampling frequency
        Fc: 10, // cutoff frequency / center frequency for bandpass, bandstop, peak
        });

    this.NDIMS = 3;
    this.iirFilters = [];

    this.reset = function() {
        for (var i=0; i<this.NDIMS; i++) {this.iirFilters[i].reinit();}
    }

    this.init = function() {
        for (var i=0; i<this.NDIMS; i++) {
            this.iirFilters[i] = new Fili.IirFilter(this.iirFilterCoeffs);
        }
    }
    //create a filter instance from the calculated coeffs
    this.lowpass = function(sample) {
        var filtered = [];
        for (var i=0; i<this.NDIMS; i++) {
            filtered[i] = this.iirFilters[i].singleStep(sample[i])
        }
        return filtered
    }
}




////////////////////////////////////////////////////////////////////////////////
// DTW COMPUTE
function dtw_compute() {

    this.models = {};

    this.distance_p1_2d = function (a, b) {
        var diff = a.map(function (i,j) {return Math.abs(i - b[j])});
        var sum = diff.reduce((a, b) => a + b, 0);
        return sum
    }

    this.compute_distance = function(A) {
        // Computes the minimum DTW distance of A against all previously recorded
        // identified segments.
        // Inputs:
        //   A: a multidimensional equispaced time series.
        // Returns:
        //   The minimum DTW distance.

        var min_key = 0;
        var min_dist = 10000;

        n_models = Object.keys(this.models).length;
        // if no models yet, store series and return
        if (n_models == 0) {
            this.models[0] = A;
        }
        // else loop over all models and find closest
        else {

            for (key in this.models) {
                var B = this.models[key];
                var dtw = new DTW(A, B, this.distance_p1_2d);
                var cur_dist = dtw.getDistance();

                if (cur_dist < min_dist) {
                    min_key = key;
                    min_dist = cur_dist;
                }
            }
            // TODO: store model only if min distance under threshold
            this.models[n_models] = A;
        }
        return [min_key, min_dist]
    }
}



////////////////////////////////////////////////////////////////////////////////
// PHASE UNWRAP
// behaves (hopefully) like np.unwrap on data stream.
function unwrap () {

    this.unwrap_last = 0;
    this.unwrap_acc = 0;
    this.unwrap_period = Math.PI;

    this.reset = function() {
        this.unwrap_acc = 0;
        this.unwrap_last = 0;
    }

    this.unwrap = function(x) {
        var diff = x + this.unwrap_acc - this.unwrap_last;

        if (Math.abs(diff) > this.unwrap_period) {
            if (diff < 0) {
                this.unwrap_acc += 2*this.unwrap_period;
            }
            if (diff > 0) {
                this.unwrap_acc -= 2*this.unwrap_period;
            }
        }
        var unwrap_x = x + this.unwrap_acc;
        this.unwrap_last = unwrap_x;
        return unwrap_x
    }
}


////////////////////////////////////////////////////////////////////////////////
// DEBUG PRINT
function db_obj() {
    this.PRINT_CNT = 0;
    this.PRINT_FRQ = 100;

    this.debug_print = function(message, data) {
        if ((this.PRINT_CNT % this.PRINT_FRQ) == 0) {
            Max.post(message, data);
        }
        this.PRINT_CNT += 1;
    }
}


module.exports = {
    lowpass: lowpass,
    unwrap: unwrap,
    dtw_compute: dtw_compute,
    timeinterp: ti_obj,
    debug_print: db_obj,
}

