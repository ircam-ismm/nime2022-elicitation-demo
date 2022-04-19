const Max = require('max-api');

PRINT_CNT = 0
PRINT_FRQ = 100
function debug_print(message, data) {
    if ((PRINT_CNT % PRINT_FRQ) == 0) {
        Max.post(message, data);
    }
    PRINT_CNT += 1;
}

module.exports = {
   debug_print: debug_print
}