/**
 * GCS Testing
 *
 * Contains a number of functions for testing different features
 *
 * Functions and constants should be prefixed with "testing_" 
*/


/// DISPLAY
const TESTING_DISPLAY_STATES = [
    "av-state-gpsfix",
    "av-state-dualboard",
    "av-state-pyro-1",
    "av-state-pyro-2",
    "av-state-pyro-3",
    "av-state-pyro-4",
    "radio-av-state",
    "radio-gse-state",
]

const TESTING_DISPLAY_ITEMS = [
    "av-accel-x",
    "av-accel-y",
    "av-accel-z",
    "av-gyro-x",
    "av-gyro-y",
    "av-gyro-z",
    "av-velocity",
    "av-mach",
    "pos-alt-m",
    "pos-alt-ft",
    "pos-maxalt-m",
    "pos-maxalt-ft",
    "pos-gps-lat",
    "pos-gps-lon",
    "aux-transducer-1",
    "aux-transducer-2",
    "aux-transducer-3",
    "aux-thermocouple-1",
    "aux-thermocouple-2",
    "aux-thermocouple-3",
    "aux-thermocouple-4",
    "aux-internaltemp",
    "aux-gasbottle-1",
    "aux-gasbottle-2",
    "aux-loadcell",
    "fs-flightstate",
    "fs-time",
    "radio-av-rssi",
    "radio-av-snr",
    "radio-av-packets",
    "radio-gse-rssi",
    "radio-gse-snr",
    "radio-gse-packets",
];

function testing_updateAllDisplayValues() {
    TESTING_DISPLAY_STATES.forEach((item) => {
        displaySetState(item, "on");
    })
    TESTING_DISPLAY_ITEMS.forEach((item, i) => {
        displaySetValue(item, i);
    });
}

/// API


/// GRAPHS


// THREE