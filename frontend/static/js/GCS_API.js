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

// API
const initialReconnectInterval = 200;
const maxReconnectInterval = 5000;

var api_socket;
var reconnectInterval = initialReconnectInterval;
var reconnectTimeout;

function scheduleReconnect() {
    reconnectTimeout = setTimeout(() => {
        reconnectInterval = Math.min(
            reconnectInterval * 2,
            maxReconnectInterval
        );
        API_socketConnect();
    }, reconnectInterval);
}

function API_socketConnect() {
    const api_url = window.location.host.split(":")[0];
    api_socket = new WebSocket(`ws://${api_url}:1887`);

    api_socket.onopen = () => {
        console.log(`connection gaming - ${api_url}`);
        clearTimeout(reconnectTimeout);
        reconnectInterval = initialReconnectInterval;
    };

    api_socket.onmessage = API_OnMessage;

    api_socket.onerror = (error) => {
        console.error("websocket error: ", error);
    };

    api_socket.onclose = () => {
        console.log("Socket closed: attempting to reconnect automatically");
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
            if (typeof rocketUpdate === "function") {
                rocketUpdate(apiData);
            }
        }
        // HANDLE GSE PACKETS
        else if ([6, 7].includes(apiLatest.id)) {
            apiData._radio = "gse";
            apiData.meta.packets = ++packetsGSE;

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

    // Return processed data
    return processedData;
}

API_socketConnect();
