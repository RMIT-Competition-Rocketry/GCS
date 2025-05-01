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
var api_socket;
var reconnectInterval = 1000;
var maxReconnectInterval = 10000;
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
    api_url = window.location.host.split(":")[0];
    api_socket = new WebSocket(`ws://${api_url}:1887`);

    api_socket.onopen = () => {
        console.log(`connection gaming - ${api_url}`);
        clearTimeout(reconnectTimeout);
        reconnectInterval = 1000;
    };

    api_socket.onmessage = API_OnMessage;

    api_socket.onerror = (error) => {
        console.error("websocket error: ", error);
        api_socket.close();
    };

    api_socket.onclose = () => {
        console.log("socket closed: attempting to reconnect");
        scheduleReconnect();
    };
}

function API_OnMessage(event) {
    try {
        //console.log(JSON.parse(event.data));

        const api_latest = JSON.parse(event.data);
        const api_data = api_latest.data;
        api_data.id = api_latest.id;

        // Additional processing of API data for display
        processDataForDisplay(api_data);

        // Send data to display
        if (api_latest.id == 3 || api_latest.id == 4 || api_latest.id == 5) {
            // AVIONICS PACKETS
            api_data._radio = "av1";
            api_data.meta.packets = ++packetsAV1;

            console.log("av1");

            // Radio module
            if (typeof displayUpdateRadio === "function") {
                console.log("radio");
                displayUpdateRadio(api_data);
            }

            // Rocket
            if (typeof rocketUpdate === "function") {
                rocketUpdate(api_data);
            }
            

            /*
            // Main display
            displayUpdateAuxData?.(api_data);
            displayUpdateAvionics?.(api_data);
            displayUpdateFlightState?.(api_data);
            displayUpdatePayload?.(api_data);
            displayUpdatePosition?.(api_data);

            // Update graphs
            graphUpdateAvionics?.(api_data);
            graphUpdatePosition?.(api_data);
            */
        } else if (api_latest.id == 6 || api_latest.id == 7) {
            // GSE PACKETS
            api_data._radio = "gse";
            api_data.meta.packets = ++packetsGSE;

            // Radio module
            if (displayUpdateRadio != undefined && typeof displayUpdateRadio === 'function') {
                displayUpdateRadio?.(api_data);
            }
        }
    } catch (error) {
        console.error("data error");
        console.error(error);
    }
}

function processDataForDisplay(api_data) {
    // Process data from the API for display

    // Acceleration
    // Determine whether to use low or high precision values
    if (api_data.accelLowX != undefined && api_data.accelHighX != undefined) {
        api_data.accelX =
            Math.abs(api_data.accelHighX) < 17
                ? api_data.accelLowX
                : api_data.accelHighX;
    }
    if (api_data.accelLowY != undefined && api_data.accelHighY != undefined) {
        api_data.accelY =
            Math.abs(api_data.accelHighY) < 17
                ? api_data.accelLowY
                : api_data.accelHighY;
    }
    if (api_data.accelLowZ != undefined && api_data.accelHighZ != undefined) {
        api_data.accelZ =
            Math.abs(api_data.accelHighZ) < 17
                ? api_data.accelLowZ
                : api_data.accelHighZ;
    }

    // Altitude
    // Track maximum altitude
    if (altitudeMax == undefined || api_data.altitude > altitudeMax) {
        altitudeMax = api_data.altitude;
    }
    api_data.altitudeMax = altitudeMax;
    return api_data;
}

API_socketConnect();
