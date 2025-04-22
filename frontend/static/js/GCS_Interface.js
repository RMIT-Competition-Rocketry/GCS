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


// UNIT CONVERSION FUNCTIONS
function metresToFeet(metres) {
    return metres * 3.28084;
}

function feetToMetres(feet) {
    return feet / 3.28084;
}


// FUNCTIONS FOR UPDATING VALUES IN THE INTERFACE
function interfaceSet(item, value, precision=2) {
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

function interfaceUpdateAvionics(data) {
    /// Update data in avionics module
    // Indicators
    /*
    interfaceSetState("av-state-gpsfix", "on");
    interfaceSetState("av-state-dualboard", "on");
    interfaceSetState("av-state-pyro-1", "on");
    interfaceSetState("av-state-pyro-2", "on");
    interfaceSetState("av-state-pyro-3", "on");
    interfaceSetState("av-state-pyro-4", "on");
    */

    // Acceleration (_g_)
    // accelLow has higher resolution, so we use that if the values are within [-16,16]
    if (data.accelLowX && data.accelHighX) {
        interfaceSet("av-accel-x", Math.abs(data.accelHighX) < 17 ? data.accelLowX : data.accelHighX);
    }

    if (data.accelLowY && data.accelHighY) {
        interfaceSet("av-accel-y", Math.abs(data.accelHighY) < 17 ? data.accelLowY : data.accelHighY);
    }

    if (data.accelLowZ && data.accelHighZ) {
        interfaceSet("av-accel-z", Math.abs(data.accelHighZ) < 17 ? data.accelLowZ : data.accelHighZ);
    }

    // Gyro (deg/s)
    if (data.gyroX) {
        interfaceSet("av-gyro-x", data.gyroX);
    }

    if (data.gyroY) {
        interfaceSet("av-gyro-y", data.gyroY);
    }

    if (data.gyroZ) {
        interfaceSet("av-gyro-z", data.gyroZ);
    }

    // Velocity (m/s)
    if (data.velocity) {
        interfaceSet("av-velocity", data.velocity);
    }

    //interfaceSet("av-mach", );
}

function interfaceUpdatePosition(data) {
    /// Update data in position module
    // Altitude
    if (data.altitude) {
        interfaceSet("pos-alt-m", data.altitude);
        interfaceSet("pos-alt-ft", Math.round(metresToFeet(data.altitude)));
    }
    
    /*
    interfaceSet("pos-maxalt-m", data.altitude);
    interfaceSet("pos-maxalt-ft", data.altitude);
    interfaceSet("pos-gps-lat", data.GPSLatitude);
    interfaceSet("pos-gps-lon", data.GPSLongitude);
    */
}