/**
 * GCS Display
 *
 * Responsible for switching tabs/pages, button logic, etc.
 * Updates stats on the webpage based on the API and handles the password screen.
 *
 * Functions and constants should be prefixed with "display"
 */

// DYNAMIC MODULE SWITCHING CODE
function displaySelectModule(selected) {
    document.querySelectorAll(".module").forEach((elem) => {
        if (elem.classList.contains(selected)) {
            elem.classList.remove("hidden");
        } else {
            elem.classList.add("hidden");
        }
    });
}

const selectedClasses = ["selected"];

// Get selected page
var selected = window.location.hash
    ? this.window.location.hash.substring(1)
    : document.querySelector("nav a").href.split("#")[1];

// Determine which modules are "selected"
displaySelectModule(selected);

// Highlight selected tab link
document
    .querySelector(`a[href='#${selected}']`)
    .classList.add(...selectedClasses);

// Switch tabs when links are pressed
document.querySelectorAll("nav a").forEach((elem) => {
    elem.addEventListener("click", (event) => {
        event.preventDefault();

        // Switch tabs
        selected = elem.href.split("#")[1];
        displaySelectModule(selected);

        // Highlight new selected tab link
        document.querySelectorAll("nav a").forEach((elem) => {
            elem.classList.remove(...selectedClasses);
        });
        document
            .querySelector(`a[href='#${selected}']`)
            .classList.add(...selectedClasses);

        if (selected == "m-ops") {
            // Single operator icon fix
            document.querySelector(`a[href='#m-password']`).classList.add(...selectedClasses);
        }

        // Update URL
        history.replaceState(null, "", `#${selected}`);

        // Dispatch page resize event (since elements are moving around)
        window.dispatchEvent(new Event("resize"));
    });
});


// FUNCTIONS FOR UPDATING DISPLAY ITEMS
var verboseLogging = false;
const indicatorStates = ["off", "on", "idle", "error"];
const timeouts = {};

function displaySetValue(item, value, precision = 2, error = false) {
    // Updates a floating point value for a display item
    if (value != undefined && !Number.isNaN(value)) {
        if (verboseLogging) console.debug(`new value %c${item}%c ${parseFloat(value).toFixed(precision)}`, 'color:orange', 'color:white');

        // Use classes instead of IDs since IDs must be unique
        // and some items occur on multiple pages
        let elements = document.querySelectorAll(`.${item}`);
        if (elements && elements.length > 0) {
            elements.forEach((elem) => {
                // Update value
                elem.value = parseFloat(value).toFixed(precision);

                // Update error state
                if (error) {
                    elem.classList.add("error");
                } else {
                    elem.classList.remove("error");
                }
            });
        }
    }
}

function displaySetString(item, string) {
    // Updates the string in a display item
    if (string != undefined) {
        if (verboseLogging) console.debug(`new string %c${item}%c ${string}`, 'color:orange', 'color:white');

        // Update all instances of item
        let elements = document.querySelectorAll(`.${item}`);
        if (elements && elements.length > 0) {
            elements.forEach((elem) => {
                // Update string
                elem.value = string;
            });
        }
    }
}

function displaySetState(item, value) {
    // Updates the state of an indicator
    if (verboseLogging) console.debug(`new state %c${item}%c ${value}`, 'color:orange', 'color:white');

    // Update all instances of item
    let elements = document.querySelectorAll(`.${item}`);
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            elem.classList.remove(...indicatorStates);

            // Convert true/false boolean values to on/error
            if (typeof value == "boolean") {
                value = value ? 1 : 3;
            }

            // Get indicator state from value
            if (value >= 0 && value < indicatorStates.length) {
                elem.classList.add(indicatorStates[value]);
            }
        });
    }
}

function displaySetActiveFlightState(item) {
    // Updates active flight state to a specific html element
    let elements = document.querySelectorAll(`.${item}`);

    if (elements && elements.length > 0) {
        // Make sure we're actually updating this
        if (elements[0].classList.contains("active")) return;

        // The active element is different, update active item
        let active = document.querySelectorAll(`.active`);
        if (active && active.length > 0) {
            active.forEach((elem) => {
                elem.classList.remove("active");
            });
        }

        // Update active item
        elements.forEach((elem) => {
            elem.classList.add("active");
        });
    }

    // Launch timer
    if (item == "fs-state-launch") {
        if (timers.launchTimestamp == 0) {
            timers.launchTimestamp = timestampApi;
        }
    }
}

// FUNCTIONS FOR UPDATING MODULES
function displayUpdateTime() {
    /// SYSTEM TIME
    if (timestampApi != 0) {
        displaySetValue("fs-time-api", timestampApi, 1);

        // Rocket launch time 
        // TODO: Find somewhere nicer to put this in the code, this is so jank
        if (timers?.launchTimestamp != 0) {
            displaySetString("fs-launch-time", `T+ ${(timestampApi - timers.launchTimestamp).toFixed(1)}`);
        }
    }
    if (timestampLocal != 0) {
        displaySetValue("fs-time-local", timestampLocal + timestampApiConnect - timeDrift, 1);
    }
}

function displayUpdateAuxData(data) {
    /// MODULE AUXDATA
    // Transducers (Bar)
    if (data?.transducer1) {
        // N2O in pressure
        displaySetValue("aux-transducer-1", data.transducer1, 1);
        hmiUpdateValue("hmi-pressure-1", data.transducer1);
    }
    if (data?.transducer2) {
        // N2O out pressure
        displaySetValue("aux-transducer-2", data.transducer2, 1);
        hmiUpdateValue("hmi-pressure-2", data.transducer2);
    }
    if (data?.transducer3) {
        // O2 pressure
        displaySetValue("aux-transducer-3", data.transducer3, 1);
        hmiUpdateValue("hmi-pressure-3", data.transducer3);
    }

    // Thermocouples (degrees Celsius)
    if (data?.thermocouple1) {
        // n2o (int) temperature
        displaySetValue("aux-thermocouple-1", data.thermocouple1, 0);
        hmiUpdateValue("HMI_N2O-INTTEMP", data.thermocouple1);
    }
    if (data?.thermocouple2) {
        // n2o #1 pressure
        displaySetValue("aux-thermocouple-2", data.thermocouple2, 0);
        hmiUpdateValue("HMI_N2O-1TEMP", data.thermocouple2);
    }
    if (data?.thermocouple3) {
        // n2o #2 pressure
        displaySetValue("aux-thermocouple-3", data.thermocouple3, 0);
        hmiUpdateValue("HMI_N2O-2TEMP", data.thermocouple3);
    }
    if (data?.thermocouple4) {
        // o2 pressure
        displaySetValue("aux-thermocouple-4", data.thermocouple4, 0);
        hmiUpdateValue("HMI_O2TEMP", data.thermocouple4);
    }

    // GSE enclosure thermocouple
    if (data?.internalTemp) {
        // internal temperature
        displaySetValue("aux-internaltemp", data.internalTemp, 1);
    }

    // Gas bottle weights
    if (data?.gasBottleWeight1) {
        // n2o #1 weight
        displaySetValue("aux-gasbottle-1", data.gasBottleWeight1, 1)
    }
    if (data?.gasBottleWeight2) {
        // n2o #2 weight
        displaySetValue("aux-gasbottle-2", data.gasBottleWeight2, 1)
    }

    // Rocket mass
    if (data?.analogVoltageInput1) {
        displaySetValue("aux-loadcell", data.analogVoltageInput1, 2);
    }

}

function displayUpdateAvionics(data) {
    /// MODULE AVIONICS
    // Indicators
    if (data?.navigationStatus) {
        // Nav state
        if (["NF"].includes(data.navigationStatus)) {
            // Red
            displaySetState("av-state-gpsfix", 3);
        } else if (["DR", "TT"].includes(data.navigationStatus)) {
            // Yellow
            displaySetState("av-state-gpsfix", 2);
        } else if (["D2", "D3", "G2", "G3", "RK"].includes(data.navigationStatus)) {
            // Green
            displaySetState("av-state-gpsfix", 1);
        }
    }

    if (data?.stateFlags) {
        if (data.stateFlags?.dualBoardConnectivityStateFlag) {
            displaySetState(
                "av-state-dualboard",
                data.stateFlags.dualBoardConnectivityStateFlag ? 1 : 3
            );
        }

        // TODO: Pyro 1,2,3,4
    }

    // Acceleration (_g_)
    // accelLow has higher resolution, so we use that if the values are within [-16,16]
    if (data.accelX != undefined) {
        displaySetValue("av-accel-x", data.accelX, 1);
    }

    if (data.accelY != undefined) {
        displaySetValue("av-accel-y", data.accelY, 1);
    }

    if (data.accelZ != undefined) {
        displaySetValue("av-accel-z", data.accelZ, 1);
    }

    // Gyro (deg/s)
    if (data.gyroX != undefined) {
        displaySetValue("av-gyro-x", data.gyroX, 1);
    }

    if (data.gyroY != undefined) {
        displaySetValue("av-gyro-y", data.gyroY, 1);
    }

    if (data.gyroZ != undefined) {
        displaySetValue("av-gyro-z", data.gyroZ, 1);
    }

    // Velocity
    if (data.velocity != undefined) {
        displaySetValue("av-velocity", data.velocity, 1);
        displaySetValue("av-velocity-ft", metresToFeet(data.velocity), 0);
    }

    // Mach speed
    if (data.mach_number != undefined) {
        displaySetValue("av-mach", data.mach_number);
    }
}

function displayUpdateSystemFlags(data) {
	if (data?.stateFlags) {
		if (data.stateFlags?.dualBoardConnectivityStateFlag) {
			displaySetState("sysflags-state-dualboard", data.stateFlags.dualBoardConnectivityStateFlag ? 1 : 0);
		}
		if (data.stateFlags?.recoveryChecksCompleteAndFlightReady) {
			displaySetState("sysflags-state-recovery", data.stateFlags.recoveryChecksCompleteAndFlightReady ? 1 : 0);
		}
		if (data.stateFlags?.payloadConnectionFlag) {
			displaySetState("sysflags-state-payload", data.stateFlags.payloadConnectionFlag ? 1 : 0);
		}
		if (data.stateFlags?.cameraControllerConnectionFlag) {
			displaySetState("sysflags-state-camera", data.stateFlags.cameraControllerConnectionFlag ? 1 : 0);
		}
	}
}

function displayUpdateFlightState(data) {
    /// MODULE FLIGHTSTATE
    if (data?.flightState) {
        let stateName = "";

        if (data.flightState == 0 || data.flightState == "PRE_FLIGHT_NO_FLIGHT_READY") {
            // Preflight (not ready)
            stateName = "Pre-flight (not ready)";
            displaySetActiveFlightState("fs-state-preflight");

        } else if (data.flightState == 1 || data.flightState == "LAUNCH") {
            // Launch
            stateName = "Launch";
            displaySetActiveFlightState("fs-state-launch");

        } else if (data.flightState == 2 || data.flightState == "COAST") {
            // Coast
            stateName = "Coast";
            displaySetActiveFlightState("fs-state-coast");

        } else if (data.flightState == 3 || data.flightState == "APOGEE") {
            // Apogee
            stateName = "Apogee";
            displaySetActiveFlightState("fs-state-apogee");

        } else if (data.flightState == 4 || data.flightState == "DESCENT" || data.flightState == "DESCENT") {
            // Descent
            stateName = "Descent";
            displaySetActiveFlightState("fs-state-descent");

        } else if (data.flightState == 5 || data.flightState == "LANDED") {
            // Landed successfully
            stateName = "Landed";
            displaySetActiveFlightState("fs-state-landed");

        } else if (data.flightState == 6 || data.flightState == 7 || data.flightState == "ON_NO") {
            // Oh shit oh fuck what the heck :(
            stateName = "Aaaaaaah!!!!";

        }

        displaySetString("fs-flightstate", stateName);
    }
}

function displayUpdatePosition(data) {
    /// MODULE POSITION
    // Altitude
    if (data.altitude != undefined) {
        displaySetValue("pos-alt-m", data.altitude, 0);
        displaySetValue("pos-alt-ft", metresToFeet(data.altitude), 0);
    }

    // Max altitude
    if (data.altitudeMax != undefined) {
        displaySetValue("pos-maxalt-m", data.altitudeMax, 0);
        displaySetValue("pos-maxalt-ft", metresToFeet(data.altitudeMax), 0);
    }

    // GPS
    if (data.GPSLatitude != undefined) {
        // Only update if reading isn't 0
        if (data.GPSLatitude != 0) {
            displaySetValue("pos-gps-lat", data.GPSLatitude, 6);
        } else {
            // Mark as stale?
        }
    }

    if (data.GPSLongitude != undefined) {
        // Only update if reading isn't 0
        if (data.GPSLongitude != 0) {
            displaySetValue("pos-gps-lon", data.GPSLongitude, 6);
        } else {
            // Mark as stale?
        }
    }

    // Nav state
    if (data?.navigationStatus) {
        displaySetString("pos-navstate", data.navigationStatus);
    }
}

function displayUpdateRadio(data) {
    /// MODULE RADIO
    if (data?.meta?.radio) {
        if (data.meta.radio == "av1") {
            // AVIONICS DATA
            // Connection indicators
            displaySetState("radio-av-state", 1);

            if (timeouts != undefined) {
                clearTimeout(timeouts?.radioAv1Idle);
                timeouts.radioAv1Idle = setTimeout(() => {
                    displaySetState("radio-av-state", 2);
                }, 1000);

                clearTimeout(timeouts?.radioAv1Error);
                timeouts.radioAv1Error = setTimeout(() => {
                    displaySetState("radio-av-state", 3);
                }, 5000);
            }

            // Update avionics radio data
            if (data?.meta?.rssi) {
                displaySetValue("radio-av-rssi", data.meta.rssi, 0);
            }

            if (data?.meta?.snr) {
                displaySetValue("radio-av-snr", data.meta.snr, 0);
            }

            if (data?.meta?.packets) {
                // Lost packets calculation
                let lostPackets = data.meta.totalPacketCountAv - data.meta.packets;

                // Display number of packets
                displaySetValue("radio-av-packets", data.meta.packets, 0);
            }

        } else if (data.meta.radio == "gse") {
            // GSE DATA
            // Connection indicators
            displaySetState("radio-gse-state", 1);

            if (timeouts != undefined) {
                clearTimeout(timeouts?.radioGseIdle);
                timeouts.radioGseIdle = setTimeout(() => {
                    displaySetState("radio-gse-state", 2);
                }, 1000);

                clearTimeout(timeouts?.radioGseError);
                timeouts.radioGseError = setTimeout(() => {
                    displaySetState("radio-gse-state", 3);
                }, 5000);
            }
            

            // Update GSE radio data
            if (data?.meta?.rssi) {
                displaySetValue("radio-gse-rssi", data.meta.rssi, 0);
            }

            if (data?.meta?.snr) {
                displaySetValue("radio-gse-snr", data.meta.snr, 0);
            }

            if (data?.meta?.packets) {
                // Lost packets calculation
                let lostPackets = data.meta.totalPacketCountGse - data.meta.packets;

                // Display number of packets
                displaySetValue("radio-gse-packets", data.meta.packets, 0);
            }
        }
    }
}

// SINGLE OPERATOR PAGE

// Continuity buttons
// function continuityActivate() {
//     const continuityA = document.getElementById("continuityA");
//     const continuityB = document.getElementById("continuityB");
//     const continuityC = document.getElementById("continuityC");
//     const continuityD = document.getElementById("continuityD");

//     continuityA.addEventListener("click", sendContinuityA)
//     continuityB.addEventListener("click", sendContinuityB)
//     continuityC.addEventListener("click", sendContinuityC)
//     continuityD.addEventListener("click", sendContinuityD)

// }

function sendContinuityA() {
    const payload = [true, false, false, false];
    continuityPayload(payload);
}

function sendContinuityB() {
    const payload = [false, true, false, false];
    continuityPayload(payload);
}

function sendContinuityC() {
    const payload = [false, false, true, false];
    continuityPayload(payload);
}

function sendContinuityD() {
    const payload = [false, false,false, true];
    continuityPayload(payload);
}

// Pop test buttons
const mainPCheckbox = document.getElementById("optionMainP");
const mainSCheckbox = document.getElementById("optionMainS");
const apogeePCheckbox = document.getElementById("optionApogeeP");
const apogeeSCheckbox = document.getElementById("optionApogeeS");
const popButton = document.getElementById("popButton");
const prompt = document.getElementById("prompt");


mainPCheckbox.addEventListener("click", validateSelection);
mainSCheckbox.addEventListener("click", validateSelection);
apogeePCheckbox.addEventListener("click", validateSelection);
apogeeSCheckbox.addEventListener("click", validateSelection);

// Only one selection at a time
mainPCheckbox.addEventListener("change", () => {
    if (mainPCheckbox.checked) {
        mainSCheckbox.checked = false;
        apogeePCheckbox.checked = false;
        apogeeSCheckbox.checked = false;
    }
    validateSelection();
});

mainSCheckbox.addEventListener("change", () => {
    if (mainSCheckbox.checked) {
        mainPCheckbox.checked = false;
        apogeePCheckbox.checked = false;
        apogeeSCheckbox.checked = false;
    }
    validateSelection();
});

apogeePCheckbox.addEventListener("change", () => {
    if (apogeePCheckbox.checked) {
        mainPCheckbox.checked = false;
        mainSCheckbox.checked = false;
        apogeeSCheckbox.checked = false;
    }
    validateSelection();
});

apogeeSCheckbox.addEventListener("change", () => {
    if (apogeeSCheckbox.checked) {
        mainPCheckbox.checked = false;
        mainSCheckbox.checked = false;
        apogeePCheckbox.checked = false;
    }
    validateSelection();
});

function validateSelection() {

    const checkedCount =
        (mainPCheckbox.checked ? 1 : 0) +
        (mainSCheckbox.checked ? 1 : 0) +
        (apogeePCheckbox.checked ? 1 : 0) +
        (apogeeSCheckbox.checked ? 1 : 0);

    if (checkedCount === 1) {
        popButton.disabled = false;
        popButton.classList.remove("pop_button_inactive");
        popButton.classList.add("pop_button_active");
        prompt.style.visibility = 'hidden';
    } else {
        popButton.disabled = true;
        popButton.classList.remove("pop_button_active");
        popButton.classList.add("pop_button_inactive");
        prompt.style.visibility = 'visible';
    }
}


popButton.addEventListener("click", function () {
    popPayload();
});


// Aux system buttons
const solenoid = document.getElementById("solenoidButton");
const modal = document.getElementById("confirmationModal");
const confirmYes = document.getElementById("confirmYes");
const confirmNo = document.getElementById("confirmNo");
const confirmText = document.getElementById("confirmText");
const solenoidCommand = document.getElementById("solenoidCommand");
let isSolenoidActive = false;

// Modal popup
solenoid.addEventListener("click", () => {
    // If manual activation is active, show a different confirmation text
    if (isSolenoidActive) {
        confirmText.textContent =
            "Are you sure you want to disable manual solenoid?";
    } else {
        confirmText.textContent = "Are you sure you want to enable manual solenoid?";
    }

    modal.classList.remove("hidden");
});

// Modal disappear when No, keep state
confirmNo.addEventListener("click", () => {
    modal.classList.add("hidden");
});

// Modal disappear when Yes, handle active/inactive states
confirmYes.addEventListener("click", () => {
    modal.classList.add("hidden");

    // If solenoid is active, deactivate it and reset switches
    if (isSolenoidActive) {
        solenoidCommand.hidden = true;
        solenoid.classList.remove("solenoid_button_active");
        solenoid.innerHTML = "Enable Manual Solenoid";
        document.querySelectorAll(".solSwitch").forEach((el) => {
            el.checked = false;
            el.disabled = true;
        });
        isSolenoidActive = false;
    } else {
        // If solenoid is inactive, activate it and switch other items
        solenoid.classList.add("solenoid_button_active");
        solenoid.innerHTML = "Disable Manual Solenoid";
        solenoidCommand.hidden = false;
        document.querySelectorAll(".solSwitch").forEach((el) => {
            el.disabled = false;
        });
        isSolenoidActive = true;
    }
    solenoidPayload();
});

// Send solenoid JSON packets to the websocket when clicked
var solenoidBools = [];
solenoidCommand.addEventListener("click", () => {
    solenoidCommand.classList.remove("opacity-60");
    solenoidCommand.classList.add("opacity-100")
    
    setTimeout(() => {
        solenoidCommand.classList.remove("opacity-100");
        solenoidCommand.classList.add("opacity-60");
        
    }, 150);

    solenoidPayload();
});


// single operator password page
window.onload = function () {
    const password = "HIVE-RMIT";
    const submit = document.getElementById("operatorSubmit");
    const incorrectWarning = document.getElementById("passIncorrect");
    const inputEnter = document.getElementById("operatorPass");

    submit.addEventListener("click", () => {
        const input = document.getElementById("operatorPass").value;
        if (input === password) {
            document.getElementById('m-ops-button').click();
            incorrectWarning.hidden = true;

        }
        else {
            incorrectWarning.hidden = false;
        }
    });

    inputEnter.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {

            if (inputEnter.value === password) {
                document.getElementById('m-ops-button').click();
                incorrectWarning.hidden = true;

            }
            else {
                incorrectWarning.hidden = false;
            }
        }
    });

};
