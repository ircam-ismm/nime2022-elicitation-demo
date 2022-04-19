// this will segment the input data based on the speed profile
autowatch = true;

var stroke = [];
var speeds = [];
var SPEED_THRESHOLD = 1.0;

function new_sample() {
    var data = arrayfromargs(arguments);
    stroke.push(data);
    // post(data);

    var speed = Math.pow(data[0], 2) + Math.pow(data[1], 2);
    speed = 10000 * speed;
    speeds.push(speed);

    post("speed:", speed, "\n");

    // find extrema over the last three recorded points
    if (stroke.length > 3) {
        var last_3 = speeds.slice(-3);

        // local minimum
        if ((last_3[0] > last_3[1]) && (last_3[2] > last_3[1])) {
            post("min: ", stroke.length, last_3[0], last_3[1], last_3[2], "\n");
            if ((last_3[1] < SPEED_THRESHOLD) || (stroke.length > 50)) {
                new_segment();
            }
        }
    }

}

function new_segment() {
// individual segment within a stroke
    post("SEGMENT [", stroke.length, "]\n");
    segment = stroke.splice(0, stroke.length-1);
    outlet(0, segment.join(" "));
}


function new_stroke() {
// new touch detected
    stroke = [];
    speeds = []
}

function end_stroke() {
// end of touch detected
    outlet(0, stroke.join(" "));
}