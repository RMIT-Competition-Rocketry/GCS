/**
 * GCS API
 *
 * Receives data from the API and loads it into memory to be accessed by other javascript modules.
 *
 * Functions and constants should be prefixed with "api_"
 */

// Global display values
var altitudeMax;
var packetsAV1 = 0;
var packetsGSE = 0;

// UNIT CONVERSION FUNCTIONS
function metresToFeet(metres) {
    return metres * 3.28084;
}

function feetToMetres(feet) {
    return feet / 3.28084;
}

function gpsToDecimal(gps) {
    // Converts the compressed GPS value into a decimal degrees coordinate
    if (gps == 0) {
        return 0;
    }

    // Split string into parts
    let [intPart, decPart] = gps.toString().split('.');
    
    // Get sign (positive or negative)
    let sign = intPart >= 0 ? 1 : -1;

    // Equations only work on positive numbers (since rounding and modulus changes in negative)
    intPart = Math.abs(intPart);
    let degrees = parseInt(intPart / 100);
    let minutes = parseInt(intPart % 100);
    let seconds = parseFloat(decPart.slice(0, 2) + '.' + decPart.slice(2));

    // Convert to decimal
    return sign * (degrees + minutes/60 + seconds/3600);
}

// API
const initialReconnectInterval = 200;
const maxReconnectInterval = 5000;

var api_socket;
var reconnectInterval = initialReconnectInterval;
var reconnectTimeout;
var connected = false;

// Reconnecting code
function scheduleReconnect() {
    reconnectTimeout = setTimeout(() => {
        reconnectInterval = Math.min(
            reconnectInterval * 2,
            maxReconnectInterval
        );
        API_socketConnect();
    }, reconnectInterval);
}
/*
function logError(message) {
    const logArea = document.getElementById('errorLogBox');
    if (logArea) {
        const timestamp = new Date().toLocaleTimeString();
        logArea.textContent += `[${timestamp}] Error: ${message}\n`;
        logArea.scrollTop = logArea.scrollHeight; // Auto scroll to bottom
    } else {
        console.error('Log area not found.');
    }
}
*/
function logMessage(message, type = "notification") {
    const logArea = document.getElementById('errorLogBox');
    if (!logArea) {
        console.error('Log area not found.');
        return;
    }

    const timestamp = new Date().toLocaleTimeString();
    logArea.textContent += `[${timestamp}] ${type === "error" ? "Error" : "Notice"}: ${message}\n`;
    logArea.scrollTop = logArea.scrollHeight;
}

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Clear timeouts when tabbed away from
        clearTimeout(reconnectTimeout); 
    } else {
        // Attempt reconnecting again
        if (connected == false) {
            scheduleReconnect();
        }
    }
});

function API_socketConnect() {
    const api_url = window.location.host.split(":")[0];
    api_socket = new WebSocket(`ws://${api_url}:1887`);

    api_socket.onopen = () => {
        connected = true;
        console.log(`Successfully connected to server at: - ${api_url}`);
        logMessage("Connected successfully", "notification");
        clearTimeout(reconnectTimeout);
        reconnectInterval = initialReconnectInterval;
    };

    api_socket.onmessage = API_OnMessage;

    api_socket.onerror = (error) => {
        connected = false;
        console.error("websocket error: ", error);
    };

    api_socket.onclose = () => {
        connected = false;
        console.log("Socket closed: attempting to reconnect automatically");
        logMessage("Connection Lost: Attempting to reconnect", "error");
        scheduleReconnect();
    };
}

function API_OnMessage(event) {
    let apiLatest, apiData;
    try {
        //console.log(JSON.parse(event.data));
        apiLatest = JSON.parse(event.data);
        apiData = processDataForDisplay(apiLatest.data, apiLatest.id);

        // Send data to display
        // HANDLE AVIONICS PACKETS
        if ([3, 4, 5].includes(apiLatest.id)) {
            apiData._radio = "av1";
            apiData.meta.packets = ++packetsAV1;

            /// AV DISPLAY VALUES
            // Radio module
            if (typeof displayUpdateRadio === "function") {
                displayUpdateRadio(apiData);
            }

            // Avionics module
            if (typeof displayUpdateAvionics === "function") {
                displayUpdateAvionics(apiData);
            }

            // Position module
            if (typeof displayUpdatePosition === "function") {
                displayUpdatePosition(apiData);
            }

            // Flight state module
            if (typeof displayUpdateFlightState === "function") {
                displayUpdateFlightState(apiData);
            }

            /// AV GRAPHS
            if (typeof graphUpdateAvionics === "function") {
                graphUpdateAvionics(apiData);
            }

            if (typeof graphUpdatePosition === "function") {
                graphUpdatePosition(apiData);
            }

            /// AV ROCKET
            // Rocket module
            if (apiLatest.id == 4) {
                if (typeof rocketUpdate === "function") {
                    rocketUpdate(apiData);
                }
            }
        }
        // HANDLE GSE PACKETS
        else if ([6, 7].includes(apiLatest.id)) {
            apiData._radio = "gse";
            apiData.meta.packets = ++packetsGSE;

            //console.log(apiData);
            checkErrorConditions(apiData);

            /// GSE DISPLAY VALUES
            // Radio module
            if (typeof displayUpdateRadio === 'function') {
                displayUpdateRadio(apiData);
            }

            // Auxilliary data module
            if (typeof displayUpdateAuxData === 'function') {
                displayUpdateAuxData(apiData);
            }

            /// GSE GRAPHS
            if (typeof graphUpdateAuxData === "function") {
                graphUpdateAuxData(apiData);
            }
            /*
            displayUpdatePayload(apiData);
            */
        }
    } catch (error) {
        console.error("Data processing error:", error);
    }
}

function checkErrorConditions(apiData) {
    Object.entries(apiData.errorFlags).forEach(([key, value]) => {
        if (value === true) {
            logMessage(`${key} flag raised`, "error");
        }
    });
/*
    if (api_data.id === 6) {
        if (api_data.thermocouple1 > 34.5) {
            logMessage("Thermocouple1 too high", "error");
            
        }
    }
    if (api_data.id === 7) {
        if (api_data.gasBottleWeight1 > )
    }
*/
}

function processDataForDisplay(apiData, apiId) {
    // Process data from the API for display
    const processedData = { ...apiData }; // Shallow copy
    processedData.id = apiId;

    // Acceleration
    // Determine whether to use low or high precision values
    if (apiData.accelLowX != undefined && apiData.accelHighX != undefined) {
        processedData.accelX =
            Math.abs(apiData.accelHighX) < 17
                ? apiData.accelLowX
                : apiData.accelHighX;
    }
    if (apiData.accelLowY != undefined && apiData.accelHighY != undefined) {
        processedData.accelY =
            Math.abs(apiData.accelHighY) < 17
                ? apiData.accelLowY
                : apiData.accelHighY;
    }
    if (apiData.accelLowZ != undefined && apiData.accelHighZ != undefined) {
        processedData.accelZ =
            Math.abs(apiData.accelHighZ) < 17
                ? apiData.accelLowZ
                : apiData.accelHighZ;
    }
    
    // Altitude
    // Track maximum altitude
    if (altitudeMax == undefined || apiData.altitude > altitudeMax) {
        altitudeMax = apiData.altitude;
    }
    processedData.altitudeMax = altitudeMax;

    // GPS position
    if (apiData.GPSLatitude != undefined) {
        processedData.GPSLatitude = gpsToDecimal(apiData.GPSLatitude);
    }
    if (apiData.GPSLongitude != undefined) {
        processedData.GPSLongitude = gpsToDecimal(apiData.GPSLongitude);
    }

    // Return processed data
    return processedData;
}

API_socketConnect();
