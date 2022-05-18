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
    keys_map = {};

    compute_distance(segment_id, A) {
        // Computes the minimum DTW distance of A against all previously recorded
        // identified segments.
        // Inputs:
        //   A: a multidimensional equispaced time series.
        // Returns:
        //   The minimum DTW distance.

        var min_key = 0;
        var min_dist = 0;
        var min_dist_pond = 0;

        var n_models = Object.keys(this.models).length;
        // if no models yet, store series and return
        if (n_models == 0) {
            this.models[segment_id] = [A];
        }
        // else loop over all models and find closest
        else {

            for (var key in this.models) {

                var B = this.models[key];
                // select one series among the group
                var C = B[Math.floor(Math.random() * B.length)];

                var dtw = new DTW(A, C, distance_fun);
                var cur_dist = dtw.getDistance();

                var cur_dist_pond = 2*cur_dist / (A.length + C.length);

                if (min_dist == 0) {
                    min_dist = cur_dist;
                    min_dist_pond = cur_dist_pond;
                }
                if (cur_dist < min_dist) {
                    min_key = key;
                    min_dist = cur_dist;
                    min_dist_pond = cur_dist_pond;
                }
            }

            // store model only if min distance under threshold
            if (min_dist < DTW_THRESHOLD) {
                min_key = parseInt(min_key);
                this.models[min_key].push(A);
            }
            else {
                min_key = segment_id;
                this.models[segment_id] = [A];
            }
        }

        return [min_key, min_dist, min_dist_pond]
    }
}


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
        res['best_id'] = dtwResult[0];
        res['min_dtw'] = dtwResult[1];
        res['min_dtw_pond'] = dtwResult[2];

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


