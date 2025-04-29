/**
 * GCS Interface
 *
 * Responsible for switching tabs/pages, button logic, etc.
 * Updates stats on the webpage based on the API and handles the password screen.
 *
 * Functions and constants should be prefixed with "interface" 
*/

// DYNAMIC MODULE SWITCHING CODE
function interfaceSelectModule(selected) {
    document.querySelectorAll(".module").forEach((elem) => {
        if (elem.classList.contains(selected)) {
            elem.classList.remove("hidden");
        } else {
            elem.classList.add("hidden");
        }
    });
}

window.addEventListener("load", function () {
    const selectedClasses = ["selected"];

    // Get selected page
    var selected = window.location.hash
        ? this.window.location.hash.substring(1)
        : document.querySelector("nav a").href.split("#")[1];

    // Determine which modules are "selected"
    interfaceSelectModule(selected);

    // Highlight selected tab link
    document.querySelector(`a[href='#${selected}']`).classList.add(...selectedClasses);

    // Switch tabs when links are pressed
    document.querySelectorAll("nav a").forEach((elem) => {
        elem.addEventListener("click", (event) => {
            event.preventDefault();

            // Switch tabs
            selected = elem.href.split("#")[1];
            interfaceSelectModule(selected);

            // Highlight new selected tab link
			document.querySelectorAll("nav a").forEach((elem) => {
				elem.classList.remove(...selectedClasses);
			});
			document.querySelector(`a[href='#${selected}']`).classList.add(...selectedClasses);

            // Update URL
            history.replaceState(null, "", `#${selected}`);

            // Dispatch page resize event (since elements are moving around)
            window.dispatchEvent(new Event("resize"));
        });
    });
});


// FUNCTIONS FOR UPDATING INTERFACE ELEMENTS
function interfaceSetValue(item, value, precision=2) {
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

function interfaceSetString(item, string) {
    // Updates a string for a display item
    let elements = document.querySelectorAll(`.${item}`);
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            // Update string
            elem.value = string;
        });
    }
}

function interfaceSetState(item, value) {
    // Updates the state of an indicator
    let elements = document.querySelectorAll(`.${item}`);
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            elem.classList.remove("on", "off", "error")

            switch (value) {
                case "error":
                    elem.classList.add('error');
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
function interfaceUpdateAuxData(data) {
    /// MODULE AUXDATA
}

function interfaceUpdateAvionics(data) {
    /// MODULE AVIONICS
    // Indicators
    if (data.stateFlags != undefined) {
        if (data.stateFlags.GPSFixFlag != undefined) {
            interfaceSetState("av-state-gpsfix", data.stateFlags.GPSFixFlag);
        }

        if (data.stateFlags.dualBoardConnectivityStateFlag != undefined) {
            interfaceSetState("av-state-dualboard", data.stateFlags.dualBoardConnectivityStateFlag);
        }

        /*
        interfaceSetState("av-state-pyro-1", "on");
        interfaceSetState("av-state-pyro-2", "on");
        interfaceSetState("av-state-pyro-3", "on");
        interfaceSetState("av-state-pyro-4", "on");
        */
    }
    
    // Acceleration (_g_)
    // accelLow has higher resolution, so we use that if the values are within [-16,16]
    if (data.accelX != undefined) {
        interfaceSetValue("av-accel-x", data.accelX);
        //GRAPH_AV_ACCEL.data.push(accelX);
        //graphRender(GRAPH_AV_ACCEL);
    }

    if (data.accelY != undefined) {
        interfaceSetValue("av-accel-y", data.accelY);
    }

    if (data.accelZ != undefined) {
        interfaceSetValue("av-accel-z", data.accelZ);
    }
    

    // Gyro (deg/s)
    if (data.gyroX != undefined) {
        interfaceSetValue("av-gyro-x", data.gyroX);
    }

    if (data.gyroY != undefined) {
        interfaceSetValue("av-gyro-y", data.gyroY);
    }

    if (data.gyroZ != undefined) {
        interfaceSetValue("av-gyro-z", data.gyroZ);
    }

    // Velocity (m/s)
    if (data.velocity != undefined) {
        interfaceSetValue("av-velocity", data.velocity);
    }

    // Mach speed
    if (data.mach_speed != undefined) {
        interfaceSetValue("av-mach", data.mach_speed);
    }
}

function interfaceUpdateContinuityCheck(data) {
    /// MODULE CONTINUITYCHECK
}

function interfaceUpdateFlags(data) {
    /// MODULE FLAGS
}

function interfaceUpdateFlightState(data) {
    /// MODULE FLIGHTSTATE
    if (data.flightState != undefined) {
        interfaceSetString("fs-flightstate", data.flightState)
    }
}

function interfaceUpdateHMI(data) {
    /// MODULE HMI
}

function interfaceUpdateOtherControls(data) {
    /// MODULE OTHERCONTROLS
}

function interfaceUpdatePayload(data) {
    /// MODULE PAYLOAD
}

function interfaceUpdatePopTest(data) {
    /// MODULE POPTEST
}

function interfaceUpdatePosition(data) {
    /// MODULE POSITION
    // Altitude
    if (data.altitude != undefined) {
        interfaceSetValue("pos-alt-m", data.altitude);
        interfaceSetValue("pos-alt-ft", metresToFeet(data.altitude), 0);
    }

    // Max altitude
    if (data.altitudeMax != undefined) {
        interfaceSetValue("pos-maxalt-m", data.altitudeMax);
        interfaceSetValue("pos-maxalt-ft", metresToFeet(data.altitudeMax), 0);
    }
    
    /*
    interfaceSetValue("pos-maxalt-m", data.altitude);
    interfaceSetValue("pos-maxalt-ft", data.altitude);
    interfaceSetValue("pos-gps-lat", data.GPSLatitude);
    interfaceSetValue("pos-gps-lon", data.GPSLongitude);
    */
}

function interfaceUpdateRadio(data) {
    /// MODULE RADIO
}

function interfaceUpdateRocket(data) {
    /// MODULE ROCKET
    // Probably call a function in GCS_Three.js
}

const mainCheckbox = document.getElementById('optionMain');
const apogeeCheckbox= document.getElementById('optionApogee');
const popButton = document.getElementById('popButton')

mainCheckbox.addEventListener('change', validateSelection);
apogeeCheckbox.addEventListener('change', validateSelection);

function validateSelection() {

    if ((mainCheckbox.checked || apogeeCheckbox.checked) && (!(mainCheckbox.checked && apogeeCheckbox.checked))) {
        popButton.disabled = false;
    } else {
        popButton.disabled = true;
    }
}

popButton.addEventListener('click', function () {
    //some sort of action
});