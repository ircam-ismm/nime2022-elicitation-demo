autowatch = true;

function list() {
    var data = arrayfromargs(arguments);
    // post(data);

    var t = data[0];
    var x = data[1];
    var y = data[2];

    var send = [t, 1, 1, x/255, y/255];

    outlet(0, send);
}
