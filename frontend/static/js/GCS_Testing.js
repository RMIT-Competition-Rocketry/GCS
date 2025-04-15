/**
 * GCS Testing
 *
 * Contains a number of functions for testing different features
 *
 * Functions and constants should be prefixed with "testing_" 
*/


/// INTERFACE
const TESTING_INTERFACE_ITEMS = [
    "av-vel-h",
    "av-vel-v",
    "av-vel-total",
    "av-accel-x-lo",
    "av-accel-x-hi",
    "av-accel-y-lo",
    "av-accel-y-hi",
    "av-accel-z-lo",
    "av-accel-z-hi",
    "av-gyro-x",
    "av-gyro-y",
    "av-gyro-z",
    "av-alt-m",
    "av-alt-ft",
    "av-maxalt-m",
    "av-maxalt-ft"
];

function testing_updateAllInterfaceValues() {
    TESTING_INTERFACE_ITEMS.forEach((item, i) => {
        interface_updateValue(item, i);
    });
}

/// API


/// DATAVIS


// THREE