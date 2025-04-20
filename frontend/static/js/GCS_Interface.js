/**
 * GCS Interface
 *
 * Responsible for switching tabs/pages, button logic, etc.
 * Updates stats on the webpage based on the API and handles the password screen.
 *
 * Functions and constants should be prefixed with "interface" 
*/

/// DYNAMIC MODULE SWITCHING CODE
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

// FUNCTIONS FOR UPDATING VALUES IN THE INTERFACE
function interfaceSet(item, value) {
    // Updates the value for a display item
    let elements = document.querySelectorAll(`.${item}`);

    // Use classes instead of IDs since IDs must be unique
    // and some items occur on multiple pages
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            // Update value
            elem.value = value;
        });
    }
}

function interfaceUpdateAvionics(data) {
    /// Update data in avionics module
    // Velocity (m/s)
    if (data.velocity) {
        interfaceSet("av-velocity", data.velocity);
    }

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
}

function interfaceUpdatePosition() {
    // Update data in position module
    interfaceSet("pos-alt-m", api_latest.data.altitude);
    /*
    interfaceSet("pos-alt-ft", api_latest.data.altitude);
    interfaceSet("pos-maxalt-m", api_latest.data.altitude);
    interfaceSet("pos-maxalt-ft", api_latest.data.altitude);
    interfaceSet("pos-gps-lat", api_latest.data.GPSLatitude);
    interfaceSet("pos-gps-lon", api_latest.data.GPSLongitude);
    */
}