const Max = require('max-api');
const cluster = require('node:cluster');
const http = require('node:http');
const process = require('node:process');

var DTW = require('dynamic-time-warping');

var utils = require('./utils.js');
// var dtw_compute = new utils.dtw_compute();

const { performance } = require('perf_hooks');


////////////////////////////////////////////////////////////////////////////////
// DTW COMPUTE
var DTW_THRESHOLD = 5;
class DtwCompute {

    models = {};
    threshold = 0;
    min_dtws = [];

    // Computes the minimum DTW distance of A against all previously recorded
    // identified segments.
    // Inputs:
    //   A: a multidimensional equispaced time series.
    // Returns:
    //   The minimum DTW distance.
    compute_distance(segment_id, A) {

        // if no models yet, store
        var n_models = Object.keys(this.models).length;
        if (n_models < 5) {
            this.models[segment_id] = [A];
        }

        var res = this.find_closest(segment_id, A);
        var min_key = res[0];
        var min_dtw = res[1];
        // console.log("find closest", min_key, min_dtw);
        this.min_dtws.push(min_dtw);
        this.update_threshold();

        if (min_dtw < this.threshold) {

            this.same_segment(segment_id, A, min_key);
        }
        else {
            this.novel_segment(segment_id, A);
        }

        return [min_key, min_dtw, this.threshold, n_models]
    }

    same_segment(segment_id, A, min_key) {
        // console.log("same segment", segment_id, min_key);
        // Max.post("same segment", segment_id, min_key);
        min_key = parseInt(min_key);
        this.models[min_key].push(A);
    }
    novel_segment(segment_id, A) {
        var min_key = segment_id;
        this.models[segment_id] = [A];
    }

    update_threshold() {
        var m = average(this.min_dtws);
        var s = standardDeviation(this.min_dtws);
        this.threshold = m + s;
    }

    find_closest(segment_id, A) {
        var min_key = 0;
        var min_dtw = 0;

        for (var key in this.models) {

            var B = this.models[key];
            // select one series among the group
            var C = B[Math.floor(Math.random() * B.length)];

            var dtw = new DTW(A, C, distance_fun);
            var cur_dist = dtw.getDistance();
            var cur_dist = cur_dist / (A.length + C.length);

            if ((min_dtw == 0) || (cur_dist < min_dtw)) {
                min_key = key;
                min_dtw = cur_dist;
            }
        }
        return [min_key, min_dtw]
    }


}

const average = arr => arr.reduce((a,b) => a + b, 0) / arr.length;

const standardDeviation = (arr, usePopulation = false) => {
  const mean = arr.reduce((acc, val) => acc + val, 0) / arr.length;
  return Math.sqrt(
    arr.reduce((acc, val) => acc.concat((val - mean) ** 2), []).reduce((acc, val) => acc + val, 0) /
      (arr.length - (usePopulation ? 0 : 1))
  );
};


function distance_fun(a, b) {
    // compute L1 between two arrays a and b
    var diff = a.map(function (i,j) {return Math.abs(i - b[j])});
    var sum = diff.reduce((a, b) => a + b, 0);
    return sum
}


dtwCompute = new DtwCompute();

////////////////////////////////////////////////////////////////////////////////
// COMMUNICATION INTERFACE
function processDtw(inputData) {
    if (cluster.isPrimary) {
        for (const id in cluster.workers) {
            cluster.workers[id].send(inputData);
        }
    }
}

const listeners = new Set();
function addListener(func) {
    listeners.add(func)
}

if (cluster.isPrimary) {
    function messageHandler(dtwResult) {
        // console.log(dtwResult);
        listeners.forEach(func => func(dtwResult));
    }

    // only one fork
    cluster.fork();

    for (const id in cluster.workers) {
        cluster.workers[id].on('message', messageHandler);
    }
} else {
    process.on('message', (inputData) => {
        segment_id = inputData['segment_id'];
        features = inputData['features'];

        res = {};
        res['then'] = inputData['now'];
        res['fl'] = features.length;
        res['segment_id'] = segment_id;
        res['worker_0'] = performance.now();

        const dtwResult = dtwCompute.compute_distance(segment_id, features);
        res['min_key'] = dtwResult[0];
        res['min_dtw'] = dtwResult[1];
        res['threshold'] = dtwResult[2];
        res['length'] = dtwResult[3];

        res['worker_1'] = performance.now();

        process.send(res);
    });
}


////////////////////////////////////////////////////////////////////////////////
// EXPORTS
module.exports = {
    processDtw,
    addListener,
}


