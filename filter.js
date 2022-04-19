const Max = require('max-api');
var Fili = require('fili');
var SG = require('ml-savitzky-golay').default;
var DTW = require("dynamic-time-warping")


// init
const path = require('path');
Max.post(`Loaded the ${path.basename(__filename)} script`);


PRINT_CNT = 0
PRINT_FRQ = 100
function debug_print(message, data) {
    if ((PRINT_CNT % PRINT_FRQ) == 0) {
        Max.post(message, data);
    }
    PRINT_CNT += 1;
}

//  Instance of a filter coefficient calculator
var iirCalculator = new Fili.CalcCascades();

// get available filters
var availableFilters = iirCalculator.available();

// calculate filter coefficients
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

last = 0;
Max.addHandler("lowpass", async (...sample) => {
    // debug_print("lowpass", sample);
    var filtered = [];
    for (var i=0; i<NDIMS; i++) {
        filtered[i] = iirFilters[i].singleStep(sample[i])
    }
    // var res = await Max.outlet("lowpass", JSON.stringify(filtered));
    filtered = filtered.map(function (num, idx) {return num.toFixed(9)});
    var res = await Max.outlet("lowpass", filtered.join(" "));
    // var res = await Max.outlet(filtered);
});


Max.addHandler("new_stroke", async (unused) => {
    Max.post("node = : new_stroke");
    // reset filters
    for (var i=0; i<NDIMS; i++) {
        iirFilters[i].reinit();
    }
});


Max.addHandler("end_stroke", async (unused) => {
});


Max.addHandler("stroke", async (unused) => {

});

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
Max.addHandler("segment", async (...segment) => {
    segment = segment[0].split(" ");
    segment = segment.map(x => JSON.parse("[" + x + "]"));

    if (segment.length > 10) {
        speed = segment.map(x => Math.pow(x[0], 2) + Math.pow(x[1], 2));
        angle = segment.map(x => Math.atan2(x[1], x[0]));
        var dA = SG(angle, 1, options);

        Max.post(angle);
        Max.post(dA); // first derivative
        Max.post(speed.length, angle.length);
    }

    // var dtw = new DTW(A, B, fun);
    // var dist = dtw.getDistance();
    // console.log(dist);

});


var fun = function (a, b) {
    var diff = a.map(function (i,j) {return Math.abs(i - b[j])});
    var sum = diff.reduce((a, b) => a + b, 0);
    return sum
}


function unravel(X) {
    return X;
}
