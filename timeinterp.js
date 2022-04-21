const Max = require('max-api');
const nj = require('numjs');

var linear = require('everpolate').linear

var firstpoint = true;

function reset() {
    Max.post("RESET!!!")
    firstpoint = true;
}

var stepsize = 10;
var last_time = 0;
var last_values = 0;

function new_sample(time, values) {
    // sample: t, [x, y, p]
    // Max.post(sample);

    // console.log("firstpoint", firstpoint);
    if (firstpoint == true) {
        Max.post("FIRSTPOINT", firstpoint);
        firstpoint = false
        last_time = time;
        last_values = values;
        return [[time].concat(values)]
    }

    starttime = last_time + (stepsize - last_time) % stepsize
    endtime = time

    time_steps = nj.arange(starttime, endtime, stepsize);

    // Max.post("time_steps LENGTH", time_steps.length);

    value_steps = values.map(function (element, index) {
        return linear(time_steps.tolist(), [last_time, time], [last_values[index], element])
    });

    value_steps = nj.array(value_steps).T.tolist();

    // console.log("value_steps", value_steps);

    last_time = time
    last_values = values

    var res = time_steps.tolist().map(function (element, index) {
        return [element].concat(value_steps[index])
    })

    return res.slice(1)
}

module.exports = {
   new_sample: new_sample,
   reset: reset
}

// Python code stream
// class StepInterpolator():
//     """Interpolate linearly between 2 sample at constant step size.
//     The step size is an integer (usually in ms) with smallest value 1.
//     When a new sample is observed earlier than stepsize, return empty.
//     """
//     def __init__(self, stepsize):
//         self.stepsize = stepsize
//         self.firstpoint = True
//
//         self.last_time = 0
//         self.last_value = 0
//         self.time_steps = np.zeros(1)
//         self.value_steps = np.zeros(1)
//
//     def new_sample(self, time, value):
//
//         starttime = self.last_time + (self.stepsize - self.last_time)%self.stepsize
//         endtime = time
//
//         self.time_steps = np.arange(starttime, endtime, self.stepsize)
//         self.value_steps = np.interp(self.time_steps, [self.last_time, time], [self.last_value, value])
//
//         self.last_time = time
//         self.last_value = value
//
//         return np.c_[self.time_steps, self.value_steps]

// Python code batch
// class TimeInterpolation():
//     """Constant time interpolation using linear interpolation between points.
//     """
//     def __init__(self, dt):
//         self.dt = dt
//
//     def __call__(self, sample):
//         """
//         Args:
//             sample: numpy array with columns representing time, x and y position.
//         Returns:
//             dataframe: evenly sample dataframe with columns ['t', 'xt', 'yt']
//         """
//         xyt = pd.DataFrame(data=sample, columns=['t', 'x', 'y'])
//         xyt['ts'] = xyt['t'] - xyt.iloc[0]['t']
//         tmax = xyt['ts'].iloc[-1]
//         ts = np.arange(0, tmax, self.dt)
//         ns = ts.shape[0]
//         x0 = np.interp(ts, xyt['ts'], xyt['x'])
//         y0 = np.interp(ts, xyt['ts'], xyt['y'])
//         res = pd.DataFrame(data=np.vstack([ts, x0, y0]).T, columns=['t', 'x', 'y'])
//         return res
