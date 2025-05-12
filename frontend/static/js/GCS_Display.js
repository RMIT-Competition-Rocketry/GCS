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
            if (value >= 0 && value < indicatorStates.length) {
                elem.classList.add(indicatorStates[value]);
            }
        });
    }
}

// FUNCTIONS FOR UPDATING MODULES
function displayUpdateTime() {
    /// SYSTEM TIME
    if (timestampApi != undefined && timestampApi != 0) {
        displaySetValue("fs-time-api", timestampApi, 3);
    }
    if (timestampLocal != undefined && timestampLocal != 0) {
        displaySetValue("fs-time-local", timestampLocal + timestampApiConnect, 3);
    }
}

function displayUpdateAuxData(data) {
    /// MODULE AUXDATA
    // Transducers
    if (data.transducer1 != undefined) {
        displaySetValue("aux-transducer-1", data.transducer1, 2);
    }
    if (data.transducer2 != undefined) {
        displaySetValue("aux-transducer-2", data.transducer2, 2);
    }
    if (data.transducer3 != undefined) {
        displaySetValue("aux-transducer-3", data.transducer3, 2);
    }

    // Thermocouples
    if (data.thermocouple1 != undefined) {
        displaySetValue("aux-thermocouple-1", data.thermocouple1, 2);
    }
    if (data.thermocouple2 != undefined) {
        displaySetValue("aux-thermocouple-2", data.thermocouple2, 2);
    }
    if (data.thermocouple3 != undefined) {
        displaySetValue("aux-thermocouple-3", data.thermocouple3, 2);
    }
    if (data.thermocouple4 != undefined) {
        displaySetValue("aux-thermocouple-4", data.thermocouple4, 2);
    }

    // Internal temperature
    if (data.internalTemp != undefined) {
        displaySetValue("aux-internaltemp", data.internalTemp, 2);
    }

    // Gas bottle weights
    if (data.gasBottleWeight1 != undefined) {
        displaySetValue("aux-gasbottle-1", data.gasBottleWeight1, 2)
    }
    if (data.gasBottleWeight2 != undefined) {
        displaySetValue("aux-gasbottle-2", data.gasBottleWeight2, 2)
    }

    // Rocket load cell weight
    if (data.analogVoltageInput1 != undefined) {
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
                data.stateFlags.dualBoardConnectivityStateFlag
            );
        }

        // TODO: Pyro 1,2,3,4
    }

    // Acceleration (_g_)
    // accelLow has higher resolution, so we use that if the values are within [-16,16]
    if (data.accelX != undefined) {
        displaySetValue("av-accel-x", data.accelX);
    }

    if (data.accelY != undefined) {
        displaySetValue("av-accel-y", data.accelY);
    }

    if (data.accelZ != undefined) {
        displaySetValue("av-accel-z", data.accelZ);
    }

    // Gyro (deg/s)
    if (data.gyroX != undefined) {
        displaySetValue("av-gyro-x", data.gyroX);
    }

    if (data.gyroY != undefined) {
        displaySetValue("av-gyro-y", data.gyroY);
    }

    if (data.gyroZ != undefined) {
        displaySetValue("av-gyro-z", data.gyroZ);
    }

    // Velocity
    if (data.velocity != undefined) {
        displaySetValue("av-velocity", data.velocity, 0);
        displaySetValue("av-velocity-ft", metresToFeet(data.velocity), 0);
    }

    // Mach speed
    if (data.mach_number != undefined) {
        displaySetValue("av-mach", data.mach_number);
    }
}

function displayUpdateFlightState(data) {
    /// MODULE FLIGHTSTATE
    if (data?.flightState) {
        let stateName = "";

        if (data.flightState == 0 || data.flightState == "PRE_FLIGHT_NO_FLIGHT_READY") {
            // Preflight (not ready)
            stateName = "Pre-flight (not ready)";

        } else if (data.flightState == 1 || data.flightState == "PRE_FLIGHT_FLIGHT_READY") {
            // Preflight (ready)
            stateName = "Pre-flight (flight ready)";

        } else if (data.flightState == 2 || data.flightState == "LAUNCH") {
            // Launch
            stateName = "Launch";

        } else if (data.flightState == 3 || data.flightState == "COAST") {
            // Coast
            stateName = "Coast";

        } else if (data.flightState == 4 || data.flightState == "APOGEE") {
            // Apogee
            stateName = "Apogee";

        } else if (data.flightState == 5 || data.flightState == "DESCENT") {
            // Descent
            stateName = "Descent";

        } else if (data.flightState == 6 || data.flightState == "LANDED") {
            // Landed successfully
            stateName = "Landed";

        } else if (data.flightState == 7 || data.flightState == "ON_NO") {
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

            clearTimeout(timeouts?.radioAv1Idle);
            timeouts.radioAv1Idle = setTimeout(() => {
                displaySetState("radio-av-state", 2);
            }, 1000);

            clearTimeout(timeouts?.radioAv1Error);
            timeouts.radioAv1Error = setTimeout(() => {
                displaySetState("radio-av-state", 3);
            }, 5000);

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

            clearTimeout(timeouts?.radioGseIdle);
            timeouts.radioGseIdle = setTimeout(() => {
                displaySetState("radio-gse-state", 2);
            }, 1000);

            clearTimeout(timeouts?.radioGseError);
            timeouts.radioGseError = setTimeout(() => {
                displaySetState("radio-gse-state", 3);
            }, 5000);

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

// Buttons


// Pop test buttons
const mainPCheckbox = document.getElementById("optionMainP");
const mainSCheckbox = document.getElementById("optionMainS");
const apogeePCheckbox = document.getElementById("optionApogeeP");
const apogeeSCheckbox = document.getElementById("optionApogeeS");
const popButton = document.getElementById("popButton");
const prompt = document.getElementById("prompt");


mainPCheckbox.addEventListener("change", validateSelection);
mainSCheckbox.addEventListener("change", validateSelection);
apogeePCheckbox.addEventListener("change", validateSelection);
apogeeSCheckbox.addEventListener("change", validateSelection);

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
    //some sort of action
});


// Aux system buttons
const solenoid = document.getElementById("solenoidButton");
const modal = document.getElementById("confirmationModal");
const confirmYes = document.getElementById("confirmYes");
const confirmNo = document.getElementById("confirmNo");
const confirmText = document.getElementById("confirmText");

let isSolenoidActive = false;

// Modal popup
solenoid.addEventListener("click", () => {
    // If manual activation is active, show a different confirmation text
    if (isSolenoidActive) {
        confirmText.textContent =
            "Are you sure you want to leave Manual Solenoid Activation?";
    } else {
        confirmText.textContent = "Are you sure you want to continue?";
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
        solenoid.classList.remove("solenoid_button_active");
        document.querySelectorAll(".solSwitch").forEach((el) => {
            el.disabled = true;
        });
        isSolenoidActive = false;
    } else {
        // If solenoid is inactive, activate it and switch other items
        solenoid.classList.add("solenoid_button_active");
        document.querySelectorAll(".solSwitch").forEach((el) => {
            el.disabled = false;
        });
        isSolenoidActive = true;
    }
});


// single operator password page
window.onload = function() {
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

    inputEnter.addEventListener("keypress", function(event) {
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