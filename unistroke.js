const Max = require('max-api');
const fs = require('fs');

const delay = ms => new Promise(res => setTimeout(res, ms));

function getRandomInt(max) {
    return Math.floor(Math.random() * max);
}

Max.addHandler("play_one", async (...sample) => {

    // erase previous stroke
    var res = await Max.outlet("cmd", "clear");

    // get random stroke from dataset
    const keys = Object.keys(parsed);
    const random_key = keys[getRandomInt(keys.length)];
    var i = random_key;

    // loop over data
    var firstpoint = true;
    for (j in parsed[i]) {
        var data = parsed[i][j];
        // position data
        var x0 = data[0];
        var x1 = x0+3;
        var y0 = data[1];
        var y1 = y0+3;
        var to_print = [x0, y0, x1, y1, 255, 0, 0];

        // delayed timestamp
        var t = data[2];
        if (firstpoint) {
            var t0 = t;
            firstpoint = false;
        }
        else {
            var delta = t - t0;
            t0 = t;
            await delay(delta);
        }
        var res = await Max.outlet("draw", to_print.join(" "));
    }
});

var parsed = new Object();

Max.addHandler("read", async (filename) => {
    let str = fs.readFileSync(filename,'utf8');
    parsed = JSON.parse(str);
    Max.post(filename, str, parsed);
});

//for testing - shows all the current objects in Max window
Max.addHandler("dump", async () => {
// function dump(){
    for(i in UI){
        for(j in UI[i]){
            Max.post(i,j,UI[i][j]);
        }
    }
});
