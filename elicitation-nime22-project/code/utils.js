const Max = require('max-api');
const nj = require('numjs');
var Fili = require('fili');
var fs = require('fs');
var Linear = require('everpolate').linear
var probable = require('probable');


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
class Debug {
    PRINT_CNT = 0;
    PRINT_FRQ = 100;

    print(message, data) {
        if ((this.PRINT_CNT % this.PRINT_FRQ) == 0) {
            Max.post(message, data);
        }
        this.PRINT_CNT += 1;
    }
}


////////////////////////////////////////////////////////////////////////////////
// LOGFILE WRITER
class Logger {

    logger = undefined;
    filename = 'log.txt';

    constructor() { // make log file name from current date+time, but using '-' as separator, macOS doesn't like ':'
        this.filename = '../data/' + (new Date()).toISOString().replace(/:/g, '-') + '.txt';
        console.log(this.filename);

        this.logger = fs.createWriteStream(this.filename, {
            flags: 'a' // 'a' means appending (old data will be preserved)
        });
        // this.log({ "logfilename": this.filename }); // start each log file with a line containing its filename
    }
    // no desctructor, autoclose on program end is on by default

    log(data) {
        this.logger.write(JSON.stringify(data) + '\n');
    }
}

///
class PDF {

    ptable = undefined;

    // construct from histogram counts in equally-spaced bins within range
    constructor(array, bounds) {
	var n = array.length;
	var table = new Array();
	var sum = 0;
	
	// create cumsum of hist freqs, mapped to bin center 
	for (var i = 0; i < n; i++) {
	    var freq = array[i];
	    if (freq > 0)
		table.push([[sum, sum + freq - 1], (i + 0.5) / n  * (bounds[1] - bounds[0]) + bounds[0] ]);
	    sum += freq;
	}
	this.ptable = probable.createRangeTable(table);
	
/* example: 
        this.ptable = probable.createRangeTable([ [[0,  24], 0],
						  [[25, 49], 1],
						  [[50, 74], 2],
						  [[75, 99], 3],
						]);
*/
    }

    draw() { return this.ptable.roll(); }
}



module.exports = {
    Lowpass,
    Unwrap,
    TimeInterpolation,
    Debug,
    Logger,
    PDF
}

