const Max = require('max-api');
const nj = require('numjs');
var Fili = require('fili');

var Linear = require('everpolate').linear

////////////////////////////////////////////////////////////////////////////////
// TIME INTERPOLATION

class TimeInterpolation {

    stepsize = 10;
    last_timestamp = 0;
    last_values = [];

    new_sample(timestamp, values, fp_timestamp) {
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
        var starttime = this.last_timestamp + (this.stepsize - this.last_timestamp) % this.stepsize;
        var endtime = timestamp;

        // fix for timestamp that happen on this.stepsize:
        // consequence of last line: res.slice(1)
        if ((endtime%this.stepsize)==0){endtime += 1;}

        var time_steps = nj.arange(starttime, endtime, this.stepsize);
        var value_steps = values.map((element, index) => {
            return Linear(time_steps.tolist(), [this.last_timestamp, timestamp], [this.last_values[index], element])},
            ); //need to pass this to map
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
class Lowpass {

    constructor() {
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

        for (var i=0; i<this.NDIMS; i++) {
            this.iirFilters[i] = new Fili.IirFilter(this.iirFilterCoeffs);
        }
    }

    reset() {
        for (var i=0; i<this.NDIMS; i++) {this.iirFilters[i].reinit();}
    }

    //create a filter instance from the calculated coeffs
    lowpass(sample) {
        var filtered = [];
        for (var i=0; i<this.NDIMS; i++) {
            filtered[i] = this.iirFilters[i].singleStep(sample[i])
        }
        return filtered
    }
}


////////////////////////////////////////////////////////////////////////////////
// PHASE UNWRAP
// behaves (hopefully) like np.unwrap on data stream.
class Unwrap {

    unwrap_last = 0;
    unwrap_acc = 0;
    unwrap_period = Math.PI;

    reset() {
        this.unwrap_acc = 0;
        this.unwrap_last = 0;
    }

    unwrap(x) {
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
    Lowpass,
    Unwrap,
    TimeInterpolation,
    debug_print: db_obj,
}

