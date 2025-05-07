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

    "av-velocity",
    "av-velocity-ft",
    "av-mach",
    "av-accel-x",
    "av-accel-y",
    "av-accel-z",
    "av-gyro-x",
    "av-gyro-y",
    "av-gyro-z",

    "fs-flightstate",
    "fs-time",
    
    "pos-alt-m",
    "pos-alt-ft",
    "pos-maxalt-m",
    "pos-maxalt-ft",
    "pos-gps-lat",
    "pos-gps-lon",
    
    "radio-av-rssi",
    "radio-av-snr",
    "radio-av-packets",
    "radio-gse-rssi",
    "radio-gse-snr",
    "radio-gse-packets",
];

const TESTING_API_3 = {
    "id": 3,
    "data": {
        "meta.rssi":1,
        "meta.snr":2,
        "flightState":3,
        "stateFlags": {
            "GPSFixFlag":1,
            "cameraControllerConnectionFlag":1,
            "dualBoardConnectivityStateFlag":1,
            "payloadConnectionFlag":1,
            "recoveryChecksCompleteAndFlightReady":1,
        },
        "accelLowX":4,
        "accelLowY":5,
        "accelLowZ":6,
        "accelHighX":7,
        "accelHighY":8,
        "accelHighZ":9,
        "gyroX":10,
        "gyroY":11,
        "gyroZ":12,
        "altitude":13,
        "velocity":14,
        "mach_number":15,
        "apogeePrimaryTestComplete":0,
        "apogeeSecondaryTestComplete":0,
        "apogeePrimaryTestResults":0,
        "apogeeSecondaryTestResults":0,
        "mainPrimaryTestComplete":0,
        "mainSecondaryTestComplete":0,
        "mainPrimaryTestResults":0,
        "mainSecondaryTestResults":0,
        "broadcastFlag":0,
    }
}


function testing_updateAllDisplayValues() {
    verboseLogging = true;

    TESTING_DISPLAY_STATES.forEach((item) => {
        displaySetState(item, "on");
    })
    TESTING_DISPLAY_ITEMS.forEach((item, i) => {
        displaySetValue(item, i);
    });

    verboseLogging = false;
}


/// API
function testing_mockApi() {
    verboseLogging = true;

    API_OnMessage({data:JSON.stringify(TESTING_API_3)});

    verboseLogging = false;
}


/// GRAPHS


// THREE