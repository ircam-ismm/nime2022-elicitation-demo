const Max = require('max-api');
const fs = require('fs');

const delay = ms => new Promise(res => setTimeout(res, ms));

// function getRandomInt(max) {
//     return Math.floor(Math.random() * max);
// }

var instantaneous = false;
Max.addHandler("instantaneous", async (...state) => {
    Max.post(state);
    instantaneous = state;
});

async function play_one(ns, key) {
    // var res = await Max.outlet("state", 1);
    // loop over data
    var firstpoint = true;
    var i = key;
    for (j in parsed[i]) {
        var data = parsed[i][j];
        // position data
        var x0 = data[0];
        var y0 = data[1];
        var x1 = x0+3;
        var y1 = y0+3;

        // to LCD
        var to_lcd = [x0, y0, x1, y1, 255, 0, 0];
        var res = await Max.outlet("lcd", to_lcd.join(" "));

        // delayed timestamp
        var t = data[2];
        if (firstpoint) {
            var t0 = t;
            firstpoint = false;
        }
        else {
            var delta = t - t0;
            t0 = t;
            if (instantaneous == false) {await delay(delta);}
        }

        // to PROCESSING
        var to_process = [t, ns, 1, 1, -1, x0/255, y0/255, 0.5]
        var res = await Max.outlet("process", to_process.join(" "));
    }

    // to PROCESSING: last point
    var to_process = [t, ns+1, 0, 1, -1, x0/255, y0/255, 0.5]
    var res = await Max.outlet("process", to_process.join(" "));
}

Max.addHandler("play_one", async () => {
    // erase previous stroke
    var res = await Max.outlet("cmd", "clear");
    // get random stroke from dataset
    const keys = Object.keys(parsed);
    const random_key = keys[Math.floor(Math.random() * keys.length)];
    Max.post("Unistroke read: ", random_key);
    var ns = 0;
    await play_one(ns, random_key);
});

Max.addHandler("play_n", async (n) => {
    const keys = Object.keys(parsed);
    // for (var i = keys.length-1; i>=0; i--) {
    var ns = 0;
    for (var i = n; i>=0; i--) {
        var key = keys.splice(Math.floor(Math.random()*keys.length), 1);
        Max.post("Unistroke read: ", key);
        var res = await Max.outlet("cmd", "clear");
        await play_one(ns, key);
        ns += 1;
    }
});

var parsed = new Object();
Max.addHandler("read", async (filename) => {
    let str = fs.readFileSync(filename,'utf8');
    parsed = JSON.parse(str);
    Max.post("File ", filename, " read ok.");
});

//for testing - shows all the current objects in Max window
Max.addHandler("dump", async () => {
    for(i in UI){
        for(j in UI[i]){
            Max.post(i,j,UI[i][j]);
        }
    }
});
