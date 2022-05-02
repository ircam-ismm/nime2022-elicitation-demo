autowatch = true;
inlets = 2;

var t = 0;
function anything() {
    // Receives either a sample key as a string, which is retrieved through
    // messagename OR the output of the savpgol filter as an array.
    if (inlet == 0) {
        t = messagename;
    }
    if (inlet == 1) {
        var data = arrayfromargs(arguments);
        var to_send = [t].concat(data);
        outlet(0, to_send);
    }
}
