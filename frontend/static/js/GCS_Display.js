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
function displaySetValue(item, value, precision = 2) {
    // Updates a floating point value for a display item
    let elements = document.querySelectorAll(`.${item}`);

    // Use classes instead of IDs since IDs must be unique
    // and some items occur on multiple pages
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            // Update value
            elem.value = parseFloat(value).toFixed(precision);
        });
    }
}

function displaySetString(item, string) {
    // Updates a string for a display item
    let elements = document.querySelectorAll(`.${item}`);
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            // Update string
            elem.value = string;
        });
    }
}

function displaySetState(item, value) {
    // Updates the state of an indicator
    let elements = document.querySelectorAll(`.${item}`);
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            elem.classList.remove("on", "off", "error");

            switch (value) {
                case "error":
                    elem.classList.add("error");
                    break;
                case "true":
                case "on":
                case true:
                    elem.classList.add("on");
                    break;
                case "false":
                case "off":
                case false:
                    elem.classList.add("off");
                    break;
            }
        });
    }
}

// FUNCTIONS FOR UPDATING MODULES
function displayUpdateAuxData(data) {
    /// MODULE AUXDATA
    // Transducers
    if (data.transducer1 != undefined) {
        displaySetValue("aux-transducer-1", data.transducer1, 1);
    }
    if (data.transducer2 != undefined) {
        displaySetValue("aux-transducer-2", data.transducer2, 1);
    }
    if (data.transducer3 != undefined) {
        displaySetValue("aux-transducer-3", data.transducer3, 1);
    }

    // Thermocouples
    if (data.thermocouple1 != undefined) {
        displaySetValue("aux-thermocouple-1", data.thermocouple1, 1);
    }
    if (data.thermocouple2 != undefined) {
        displaySetValue("aux-thermocouple-2", data.thermocouple2, 1);
    }
    if (data.thermocouple3 != undefined) {
        displaySetValue("aux-thermocouple-3", data.thermocouple3, 1);
    }
    if (data.thermocouple4 != undefined) {
        displaySetValue("aux-thermocouple-4", data.thermocouple4, 1);
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
    
}

function displayUpdateAvionics(data) {
    /// MODULE AVIONICS
    // Indicators
    if (data.stateFlags != undefined) {
        if (data.stateFlags.GPSFixFlag != undefined) {
            displaySetState("av-state-gpsfix", data.stateFlags.GPSFixFlag);
        }

        if (data.stateFlags.dualBoardConnectivityStateFlag != undefined) {
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

    // Velocity (m/s)
    if (data.velocity != undefined) {
        displaySetValue("av-velocity", data.velocity);
    }

    // Mach speed
    if (data.mach_number != undefined) {
        displaySetValue("av-mach", data.mach_number);
    }
}

function displayUpdateContinuityCheck(data) {
    /// MODULE CONTINUITYCHECK
}

function displayUpdateFlags(data) {
    /// MODULE FLAGS
}

function displayUpdateFlightState(data) {
    /// MODULE FLIGHTSTATE

    // TODO:
    // - Flight timer
    // - Human readable flight state values

    if (data.flightState != undefined) {
        displaySetString("fs-flightstate", data.flightState);
    }
}

function displayUpdateHMI(data) {
    /// MODULE HMI
}

function displayUpdateOtherControls(data) {
    /// MODULE OTHERCONTROLS
}

function displayUpdatePayload(data) {
    /// MODULE PAYLOAD
}

function displayUpdatePopTest(data) {
    /// MODULE POPTEST
}

function displayUpdatePosition(data) {
    /// MODULE POSITION
    // Altitude
    if (data.altitude != undefined) {
        displaySetValue("pos-alt-m", data.altitude);
        displaySetValue("pos-alt-ft", metresToFeet(data.altitude), 0);
    }

    // Max altitude
    if (data.altitudeMax != undefined) {
        displaySetValue("pos-maxalt-m", data.altitudeMax);
        displaySetValue("pos-maxalt-ft", metresToFeet(data.altitudeMax), 0);
    }

    // GPS
    if (data.GPSLatitude != undefined) {
        displaySetString("pos-gps-lat", data.GPSLatitude);
    }

    if (data.GPSLongitude != undefined) {
        displaySetString("pos-gps-lon", data.GPSLongitude);
    }
}

function displayUpdateRadio(data) {
    /// MODULE RADIO
    // TODO - Connection indicators

    if (data.meta != undefined) {
        if (data._radio == "av1") {
            // AVIONICS DATA
            if (data.meta.rssi != undefined) {
                displaySetValue("radio-av-rssi", data.meta.rssi, 0);
            }

            if (data.meta.snr != undefined) {
                displaySetValue("radio-av-snr", data.meta.snr, 1);
            }

            if (data.meta.packets != undefined) {
                displaySetValue("radio-av-packets", data.meta.packets, 0);
            }
        } else if (data._radio == "gse") {
            // GSE DATA
            if (data.meta.rssi != undefined) {
                displaySetValue("radio-gse-rssi", data.meta.rssi, 0);
            }

            if (data.meta.snr != undefined) {
                displaySetValue("radio-gse-snr", data.meta.snr, 1);
            }

            if (data.meta.packets != undefined) {
                displaySetValue("radio-gse-packets", data.meta.packets, 0);
            }
        }
    }
}

// Buttons
const mainCheckbox = document.getElementById("optionMain");
const apogeeCheckbox = document.getElementById("optionApogee");
const popButton = document.getElementById("popButton");
const prompt = document.getElementById("prompt");

mainCheckbox.addEventListener("change", validateSelection);
apogeeCheckbox.addEventListener("change", validateSelection);

mainCheckbox.addEventListener("change", () => {
    if (mainCheckbox.checked) {
        apogeeCheckbox.checked = false;
    }
    validateSelection();
});

apogeeCheckbox.addEventListener("change", () => {
    if (apogeeCheckbox.checked) {
        mainCheckbox.checked = false;
    }
    validateSelection();
});

function validateSelection() {
    if (
        (mainCheckbox.checked || apogeeCheckbox.checked) &&
        !(mainCheckbox.checked && apogeeCheckbox.checked)
    ) {
        popButton.disabled = false;
        popButton.classList.remove("pop_button_inactive");
        popButton.classList.add("pop_button_active");
        prompt.hidden = true;
    } else {
        popButton.disabled = true;
        popButton.classList.remove("pop_button_active");
        popButton.classList.add("pop_button_inactive");
        prompt.hidden = false;
    }
}

popButton.addEventListener("click", function () {
    //some sort of action
});

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
