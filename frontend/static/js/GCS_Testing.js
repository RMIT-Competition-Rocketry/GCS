/**
 * GCS Testing
 *
 * Contains a number of functions for testing different features
 *
 * Functions and constants should be prefixed with "testing_" 
*/


/// INTERFACE
const TESTING_INTERFACE_ITEMS = [
    "av-velocity",
    "av-accel-x",
    "av-accel-y",
    "av-accel-z",
    "av-gyro-x",
    "av-gyro-y",
    "av-gyro-z",
    "pos-alt-m",
    "pos-alt-ft",
    "pos-maxalt-m",
    "pos-maxalt-ft",
    "pos-gps-lat",
    "pos-gps-lon",
];

function testing_updateAllInterfaceValues() {
    TESTING_INTERFACE_ITEMS.forEach((item, i) => {
        interfaceSet(item, i);
    });
}

/// API


/// DATAVIS


// THREE