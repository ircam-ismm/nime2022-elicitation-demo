autowatch = true;
inlets = 2;

var t = 0;
function anything() {
    var data = arrayfromargs(arguments);

    if (inlet == 0) {
        t = data[0];
    }
    if (inlet == 1) {
        var to_send = [t].concat(data);
        outlet(0, to_send);
    }
    // post("inlet", inlet, data, "\n");
    var data = arrayfromargs(arguments);
}
