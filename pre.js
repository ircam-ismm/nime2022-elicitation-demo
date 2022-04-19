autowatch = true;
outlets = 2;

// receives "raw" input from sensel
// adds a timestamp
// filter the finger or interest
// for the moment, only finger 1 is let through

PRINT_CNT = 0
PRINT_FRQ = 100
function debug_print(data) {
    if ((PRINT_CNT % PRINT_FRQ) == 0) {
        post(data, "\n");
    }
    PRINT_CNT += 1;
}

var new_stroke = false;
var first_point = [];

function state_change() {
    var state = arrayfromargs(arguments);
    new_stroke = (state == 1);
    if (new_stroke) {
        outlet(1, "new_stroke");
        post("new stroke\n");
    }
    else {
        post("end stroke\n");
        outlet(1, "end_stroke");
    }
}

function new_sample() {
    var data = arrayfromargs(arguments);
    xyp = data.slice(-3);

    // store the touchdown and send relative position thereafter
    if (new_stroke) {
        post("store touchdown", xyp, "\n");
        first_point = xyp;
        first_point[2] = 0; // initial pressure is always 0
        new_stroke = false;
    }

    // substract current position from first stroke point touchdown
    var finger = data[1];
    if (finger == 1) {
        outlet(0, xyp.map(function (num, idx) { return num-first_point[idx] }));
    }
}