const Max = require('max-api');
const cluster = require('node:cluster');
const http = require('node:http');
const process = require('node:process');

var utils = require('./utils.js');
var dtw_compute = new utils.dtw_compute();

const { performance } = require('perf_hooks');


function processDtw(inputData) {
    if (cluster.isPrimary) {
        for (const id in cluster.workers) {
            // Max.post("send");
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
        console.log(dtwResult);
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
        const dtwResult = dtw_compute.compute_distance(segment_id, features);
        res = inputData;
        res = {};
        res['then'] = inputData['now'];
        res['segment_id'] = segment_id;
        res['best_id'] = dtwResult[0];
        res['min_dtw'] = dtwResult[1];
        res['now'] = performance.now();
        process.send(res);
    });
}

module.exports = {
    processDtw,
    addListener,
}

// class Obk {
//     constructor(arg) {
//     }
// }
// const Clqdaawd = function() {
// }
