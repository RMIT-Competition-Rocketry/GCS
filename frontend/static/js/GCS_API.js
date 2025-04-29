/**
 * GCS API
 *
 * Receives data from the API and loads it into memory to be accessed by other javascript modules.
 *
 * Functions and constants should be prefixed with "api_"
 */

// Global interface values
var altitudeMax;

// UNIT CONVERSION FUNCTIONS
function metresToFeet(metres) {
    return metres * 3.28084;
}

function feetToMetres(feet) {
    return feet / 3.28084;
}

// API
let api_socket;
let reconnectInterval = 1000;
let maxReconnectInterval = 10000;
let reconnectTimeout;
let api_latest = {};

function scheduleReconnect() {
    reconnectTimeout = setTimeout(() => {
        reconnectInterval = Math.min(reconnectInterval * 2, maxReconnectInterval);
        connectSocket();
    }, reconnectInterval);
}

function API_socketConnect() {
    api_socket = new WebSocket("ws://localhost:1887");

	api_socket.onopen = () => {
		console.log("connection gaming");
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
        const api_latest = JSON.parse(event.data);
		const api_data = api_latest.data;

        //console.log(Object.keys(api_latest.data));
        //console.log(api_latest.data)

		// Process data from the API for display
		// Acceleration
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
		if (
			api_data.accelLowZ != undefined &&
			api_data.accelHighZ != undefined
		) {
			api_data.accelZ =
				Math.abs(api_data.accelHighZ) < 17
					? api_data.accelLowZ
					: api_data.accelHighZ;
		}

		// Altitude
		if (altitudeMax == undefined || api_data.altitude > altitudeMax) {
			altitudeMax = api_data.altitude;
		}
		api_data.altitudeMax = altitudeMax;

        // Send data to site
        if (api_latest.id == 3) {
            // Update interface modules
            interfaceUpdateRadio(api_data); // Header

            interfaceUpdateAuxData(api_data); // Main interface
            interfaceUpdateAvionics(api_data);
            interfaceUpdateFlightState(api_data);
            interfaceUpdatePayload(api_data);
            interfaceUpdatePosition(api_data);
            interfaceUpdateRocket(api_data);

            interfaceUpdateContinuityCheck(api_data); // Single operator page
            interfaceUpdateFlags(api_data);
            interfaceUpdateOtherControls(api_data);
            interfaceUpdatePopTest(api_data);

            interfaceUpdateHMI(api_data); // HMI

			// Update graphs
			graphUpdateAvionics(api_data);
			graphUpdatePosition(api_data);

            // Update rocket 
            if (typeof rocketUpdate === 'function') rocketUpdate(api_data);

        }
    } catch (error) {
        console.error("data error");
		console.error(error);
    }
}

API_socketConnect();
