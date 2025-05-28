/**
 * GCS API
 *
 * Receives data from the API and loads it into memory to be accessed by other javascript modules.
 *
 * Functions and constants should be prefixed with "api_"
 */

// Constants
const initialReconnectInterval = 200;   // Initial reconnection wait time
const maxReconnectInterval = 5000;      // Maximum amount of time between reconnect attempts
const graphRenderRate = 20;     // FPS for rendering graphs

// API connection
var apiSocket;
var reconnectInterval = initialReconnectInterval;
var reconnectTimeout;
var connected = false;
var then, now, fpsInterval;

// Logging
const logSocket = true;
const logIncomingMessages = false;
const errors = [];

// Global display values
var altitudeMax;
var packetsAV1 = 0;
var packetsAV1offset = 0;
var packetsGSE = 0;
var packetsGSEoffset = 0;
var timestampLocalLoad = Date.now(); // Timestamp upon page load (refreshed with API to keep time-alignment)
var timestampLocal = 0; // Local timekeeping (for page to keep updating even if API stops sending signals)
var timestampApi = 0; // Timestamp sent by the API
var timestampApiConnect; // First API timestamp sent upon connection with API
var timeDrift;
const timers = {
    gasFillTimer: 0,
    launchTimestamp: 0,
}

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

// Animation/timing code
function startAnimating() {
    fpsInterval = 1000 / graphRenderRate;
    then = window.performance.now();
    animate();
}
startAnimating();
function animate(newtime) {
    requestAnimationFrame(animate);

    // Calculate time since last loop
    let now = newtime;
    let elapsed = now - then;

    // Rerender if enough time has elapsed
    if (elapsed > (fpsInterval)) {
        then = now - (elapsed % fpsInterval);

        // Rerender graphs
        if (typeof graphRequestRender === "function") {
            graphRequestRender();
        }

        // Increment time (so if we stop getting packets, time moves forward)
        timestampLocal = (Date.now() - timestampLocalLoad) / 1000;
        if (displayUpdateTime != undefined) {
            displayUpdateTime();
        }
    }
}

// Logging code
function logMessage(message, type = "notification") {
    // Log to browser console
    console.log(type, message);

    // Make sure log area exists
    const logArea = document.getElementById('errorLogBox');
    if (!logArea) {
        console.error('Log area not found.');
        return;
    }

    // Add new error to log
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('span');
    line.className = type === "error" ? "text-red-400 block" : "text-white block";
    line.textContent = `[${timestamp}] ${type === "error" ? "Error" : "Notice"}: ${message}`;

    logArea.appendChild(line);

    // Limit lines
    const maxlines = 16;
    while (logArea.children.length > maxlines) {
        logArea.removeChild(logArea.firstChild);
    }

    // Scroll to bottom of log
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
    const ws_url = `ws://${api_url}:1887`;
    apiSocket = new WebSocket(ws_url);

    console.log(
        "Attempting to open WebSocket connection to",
        ws_url,
        "\nInitial WebSocket readyState:",
        apiSocket.readyState
    ); // 0 = CONNECTING

    // Socket connected
    apiSocket.onopen = () => {
        connected = true;
        timestampApiConnect = undefined;
        if (logSocket)
            console.log(`Successfully connected to server at: - ${api_url}`);
        logMessage("Successfully connected", "notification");
        clearTimeout(reconnectTimeout);
        reconnectInterval = initialReconnectInterval;
    };

    // Socket received message
    apiSocket.onmessage = API_OnMessage;

    // Socket error
    apiSocket.onerror = (error) => {
        connected = false;
        timestampApiConnect = undefined;
        console.error("Websocket error: ", error);
    };

    // Socket closed
    apiSocket.onclose = () => {
        connected = false;
        timestampApiConnect = undefined;

        // Log on browser console
        console.warn(
            "Socket closed",
            {
                wasClean: event.wasClean,
                code: event.code,
                reason: event.reason,
            },
            "Attempting to reconnect automatically"
        );

        // Log on page
        logMessage("Connection lost: Attempting to reconnect", "error");

        // Attempt reconnecting
        scheduleReconnect();
    };

    // Monitor readystate every 10 seconds
    setInterval(() => {
        if (apiSocket)
            console.info("WebSocket readyState:", apiSocket.readyState);
    }, 10000);
}
API_socketConnect();

// Handle incoming data through the API socket
function API_OnMessage(event) {
    if (logIncomingMessages) console.log('Message from server:', event.data);

    let apiLatest, apiData;
    try {
        // Handle incoming data
        apiLatest = JSON.parse(event.data);
        apiData = processDataForDisplay(apiLatest.data, apiLatest.id);

        // Flag data for errors
        checkErrorConditions(apiData);

        // Handle different packet types
        if (apiData.id == 2) {
            ///// ----- SINGLE OPERATOR PACKETS ----- /////
            //
            
        } else if (apiData.id == 3 || apiData.id == 4) {
            ///// ----- AVIONICS PACKETS ----- /////
            // Display values
            if (typeof displayUpdateRadio === "function") {
                displayUpdateRadio(apiData);
            }
            if (typeof displayUpdateAvionics === "function") {
                displayUpdateAvionics(apiData);
            }
            if (typeof displayUpdatePosition === "function") {
                displayUpdatePosition(apiData);
            }
            if (typeof displayUpdateFlightState === "function") {
                displayUpdateFlightState(apiData);
            }
			if (typeof displayUpdateSystemFlags === "function") {
				displayUpdateSystemFlags(apiData);
			}

            // Graphs
            if (typeof graphUpdateAvionics === "function") {
                graphUpdateAvionics(apiData);
            }
            if (typeof graphUpdatePosition === "function") {
                graphUpdatePosition(apiData);
            }

            // Rocket visualisation
            if (apiData.id == 4) {
                if (typeof rocketUpdate === "function") {
                    rocketUpdate(apiData);
                }
            }

        } else if (apiData.id == 5) {
            ///// ----- PAYLOAD PACKETS ----- /////
            //

        } else if (apiData.id == 6 || apiData.id == 7) {
            ///// ----- GSE PACKETS ----- /////
            // Display values
            if (typeof displayUpdateRadio === 'function') {
                displayUpdateRadio(apiData);
            }
            if (typeof displayUpdateAuxData === 'function') {
                displayUpdateAuxData(apiData);
            }

            // Graphs
            if (typeof graphUpdateAuxData === "function") {
                graphUpdateAuxData(apiData);
            }
        }

    } catch (error) {
        console.error("Data processing error:", error);
    }
}

// Check data for error conditions
// As defined in spreadsheet
const errorConditions = [
    // Thermocouples
    {
        ids: ["thermocouple1", "thermocouple2", "thermocouple3", "thermocouple4"],
        message: "flag raised",
        error: {
            max: 34.5,
        },
        discard: {
            min: -100,
            max: 500,
        },
    },
    // Transducers
    {
        ids: ["transducer1", "transducer2", "transducer3"],
        message: "flag raised",
        error: {
            max: 64.5
        },
        discard: {
            min: -100,
            max: 500
        },
    },
    // Gas bottles
    {
        ids: ["gasBottleWeight1", "gasBottleWeight2"],
        message: "out of range",
        error: {
            min: 15.1,
            max: 19
        },
        discard: {
            min: -1,
            max: 100
        }
    }
];

function checkErrorConditions(apiData) {
    // Get error flags from the API and use as overrides
    const errorOverrides = [];
    if (apiData.errorFlags != undefined) {
        Object.entries(apiData.errorFlags).forEach(([key, value]) => {
            if (value === true) {
                errorOverrides.push(key);
            }
        });
    }

    // Iterate over all error conditions
    errorConditions.forEach((errorCondition) => {
        // Error conditions may apply equivalently to multiple data IDs
        errorCondition.ids.forEach((id) => {

            // Make sure the ID is defined within the current packet
            if (Object.keys(apiData).indexOf(id) != -1 && apiData[id] != undefined) {
                const apiDataValue = apiData[id];
                if (apiDataValue != undefined) {
                    
                    // Define error key
                    const errorKey = `${id}Error`;
                    let isError = false;
                    let isErrorApi = errorOverrides.indexOf(errorKey) != -1;
                    let isDiscard = false;

                    // Check error ranges if the value is a number
                    if (typeof apiDataValue == "number") {
                        // Check against error ranges
                        if (errorCondition?.error) {
                            if (errorCondition.error?.min && apiDataValue < errorCondition.error.min) {
                                isError = true;
                            }
                            if (errorCondition.error?.max && apiDataValue > errorCondition.error.max) {
                                isError = true;
                            }
                        }

                        // Check against discard ranges (corrupted data)
                        if (errorCondition?.discard) {
                            if (errorCondition.discard?.min && apiDataValue < errorCondition.discard.min) {
                                isDiscard = true;
                            }
                            if (errorCondition.discard?.max && apiDataValue > errorCondition.discard.max) {
                                isDiscard = true;
                            }
                        }
                    }

                    isError ||= isErrorApi;

                    // Check errors against current system status
                    if (isError && errors.indexOf(errorKey) == -1) {
                        // If error, log error and raise flag
                        logMessage(`${errorKey} ${errorCondition.message}`, "error");
                        errors.push(errorKey);
                    } else if (!isError && errors.indexOf(errorKey) != -1) {
                        // If not error, remove from errors flags
                        logMessage((`${errorKey} resolved`));
                        errors.splice(errors.indexOf(errorKey), 1);
                    }

                    // Check for discards
                    if (isDiscard) {
                        apiData[id] = NaN; // Flag invalid value with NaN
                    }
                }
            }
        });
    });
}

function processDataForDisplay(apiData, apiId) {
    // Process data from the API for display
    const processedData = { ...apiData }; // Shallow copy
    processedData.id = apiId;

    if (apiData?.meta) {
        // Timestamp, synchronization and connection
        if (apiData.meta?.timestampS) {
            if (timestampApi) {
                timestampApi = Math.max(timestampApi, apiData.meta.timestampS);
            } else {
                timestampApi = apiData.meta.timestampS;
            }

            if (timestampApiConnect == undefined) {
                timestampApiConnect = timestampApi;
                timestampLocalLoad = Date.now();
            } else {
                // Code to synchronise local time with GSE time if it gets too far behind
                timeDrift = timestampLocal - (timestampApi - timestampApiConnect);

                // Time drift
                // timeDrift > 0 means LOCAL is ahead of GSE
                // timeDrift < 0 means GSE is ahead of LOCAL
                // Ideally there's no time drift at all, but if there is it's used to update the time
                //console.log(timeDrift);
            }
        }

        // Packets
        if ([3, 4, 5].includes(apiId)) {
            if (apiData.meta?.totalPacketCountAv) {
                if (packetsAV1 == 0) {
                    packetsAV1offset = apiData.meta.totalPacketCountAv - 1;
                }
                processedData.meta.totalPacketCountAv = apiData.meta.totalPacketCountAv - packetsAV1offset;
            }

            processedData.meta.radio = "av1";
            processedData.meta.packets = ++packetsAV1;

        } else if ([6, 7].includes(apiId)) {
            if (apiData.meta?.totalPacketCountGse) {
                if (packetsGSE == 0) {
                    packetsGSEoffset = apiData.meta.totalPacketCountGse - 1;
                }
                processedData.meta.totalPacketCountGse = apiData.meta.totalPacketCountGse - packetsGSEoffset;
            }

            processedData.meta.radio = "gse";
            processedData.meta.packets = ++packetsGSE;
            
        }
    }

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

// UNIT CONVERSION FUNCTIONS
function metresToFeet(metres) {
    if (metres == undefined || isNaN(metres)) return undefined;
    return metres * 3.28084;
}

function feetToMetres(feet) {
    if (feet == undefined || isNaN(feet)) return undefined;
    return feet / 3.28084;
}

function gpsToDecimal(gps) {
    // Converts the compressed GPS value into a decimal degrees coordinate
    if (gps == undefined || isNaN(gps) || gps == 0) return 0;

    // Split string into parts
    let [intPart, decPart] = gps.toString().split('.');
    if (decPart == undefined) {
        decPart = 0;
    }
    
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

// Single Operator Functionality
function apiSendSolenoids() {
    // Sends a Solenoid request to the WebSocket
    const solenoidPayloadData = [isSolenoidActive];
    document.querySelectorAll(".solSwitch").forEach((el, index) => {
        console.log(`Solenoid ${index + 1}: ${el.checked}`);
        solenoidPayloadData[index + 1] = el.checked;
    });

    const packet = JSON.stringify({
        id: 9,
        data: {
            manualEnabled: isSolenoidActive,
            solenoid1High: solenoidPayloadData[1],
            solenoid2High: solenoidPayloadData[2],
            solenoid3High: solenoidPayloadData[3],
        }
    });

    if (apiSocket.readyState === WebSocket.OPEN) {
        apiSocket.send(packet);
        console.log('Sent solenoid JSON:', packet);
    } else {
        console.warn('WebSocket not open. ReadyState:', apiSocket.readyState);
    }
};

function apiSendPopTest() {
    // Sends a Pop Test request to the websocket
    const packet = JSON.stringify({
        id: 255,
        data: {
            mainPrimary: mainPCheckbox.checked,
            mainSecondary: mainSCheckbox.checked,
            apogeePrimary: apogeePCheckbox.checked,
            apogeeSecondary: apogeeSCheckbox.checked,
        }
    });

    if (apiSocket.readyState === WebSocket.OPEN) {
        apiSocket.send(packet);
        console.log('Sent pop test JSON:', packet);
    } else {
        console.warn('WebSocket not open. ReadyState:', apiSocket.readyState);
    }
};

function apiSendContinuityCheck(payload) {
    // Sends a Continuity Check request to the WebSocket
    const packet = JSON.stringify({
        id: 254,
        data: {
            continuityA: payload[0] == 1,
            continuityB: payload[1] == 1,
            continuityC: payload[2] == 1,
            continuityD: payload[3] == 1,
        }
    });

    if (apiSocket.readyState === WebSocket.OPEN) {
        apiSocket.send(packet);
        console.log('Sent continuity JSON:', packet);
    } else {
        console.warn('WebSocket not open. ReadyState:', apiSocket.readyState);
    }
};

function apiSendCameraSwitch() {
    // Send a Camera Switch request to the WebSocket
    const camera = document.getElementById("cameraSwitch");
    if (camera == undefined) {
        console.error("cameraSwitch element not found");
        return;
    }

    const packet = JSON.stringify({
        id: 253,
        data: {
            cameraStatus: camera.checked == true,
        }
    });

    if (apiSocket.readyState === WebSocket.OPEN) {
        apiSocket.send(packet);
        console.log('Sent camera status:', packet);
    } else {
        console.warn('WebSocket not open. ReadyState:', apiSocket.readyState);
    }
}
