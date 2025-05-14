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
const maxDesync = 1/graphRenderRate;  // Max desync (s) before local time realigns itself with GSE 

// API connection
var apiSocket;
var reconnectInterval = initialReconnectInterval;
var reconnectTimeout;
var connected = false;
var then, now, fpsInterval;

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
    apiSocket = new WebSocket(`ws://${api_url}:1887`);

    apiSocket.onopen = () => {
        connected = true;
        timestampApiConnect = undefined;
        console.log(`Successfully connected to server at: - ${api_url}`);
        logMessage("Connected successfully", "notification");
        clearTimeout(reconnectTimeout);
        reconnectInterval = initialReconnectInterval;
    };

    apiSocket.onmessage = API_OnMessage;

    apiSocket.onerror = (error) => {
        connected = false;
        timestampApiConnect = undefined;
        console.error("websocket error: ", error);
    };

    apiSocket.onclose = () => {
        connected = false;
        timestampApiConnect = undefined;
        console.log("Socket closed: attempting to reconnect automatically");
        logMessage("Connection Lost: Attempting to reconnect", "error");
        scheduleReconnect();
    };
}
API_socketConnect();

function API_OnMessage(event) {
    let apiLatest, apiData;
    try {
        // Handle incoming data
        apiLatest = JSON.parse(event.data);
        apiData = processDataForDisplay(apiLatest.data, apiLatest.id);

        apiData.errors = [];
        // Flag data for errors
        checkErrorConditions(apiData);

        
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

function checkErrorConditions(apiData) {
    if (true) {
        if (apiData.errorFlags != undefined) {
            Object.entries(apiData.errorFlags).forEach(([key, value]) => {
                if (value === true) {
                    logMessage(`${key} flag raised`, "error");
                    apiData.errors.push(key);
                }
            });
        }

        if (apiData.id === 6) {
            if (apiData.thermocouple1 > 34.5 && !apiData.errors.includes(thermocouple1Error)) {
                logMessage("thermocouple1Error flag raised", "error");
                apiData.errors.push("thermocouple1Error");
            }
            if (apiData.thermocouple2 > 34.5 && !apiData.errors.includes(thermocouple2Error)) {
                logMessage("thermocouple2Error flag raised", "error");
                apiData.errors.push("thermocouple2Error");
            }
            if (apiData.thermocouple3 > 34.5 && !apiData.errors.includes(thermocouple3Error)) {
                logMessage("thermocouple3Error flag raised", "error");
                apiData.errors.push("thermocouple3Error");
            }
            if (apiData.thermocouple4 > 34.5 && !apiData.errors.includes(thermocouple4Error)) {
                logMessage("thermocouple4Error flag raised", "error");
                apiData.errors.push("thermocouple4Error");
            }
            
            if (apiData.transducer1 > 34.5 && !apiData.errors.includes(transducer1Error)) {
                logMessage("transducer1Error flag raised", "error");
                apiData.errors.push("transducer1Error");
            }
            if (apiData.transducer2 > 34.5 && !apiData.errors.includes(transducer2Error)) {
                logMessage("transducer2Error flag raised", "error");
                apiData.errors.push("transducer2Error");
            }
            if (apiData.transducer3 > 34.5 && !apiData.errors.includes(transducer3Error)) {
                logMessage("transducer3Error flag raised", "error");
                apiData.errors.push("transducer3Error");
            }
        }
        if (apiData.id === 7) {
            if (apiData.gasBottleWeight1 > 19 || apiData.gasBottleWeight1 < 15.1) {
                logMessage("Gas bottle 1 weight not within target range", "error");
            }
            if (apiData.gasBottleWeight2 > 19 || apiData.gasBottleWeight2 < 15.1) {
                logMessage("Gas bottle 2 weight not within target range", "error");
            }
        }
    }
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

// Test function
apiSocket.addEventListener('open', () => {
    console.log('Socket connection opened');
});

apiSocket.addEventListener('message', (event) => {
    console.log('Message from server:', event.data);
});

// Test function
function testJSON() {
    const payload = {
        id: 9,
        data: {
            solenoid1High: false,
            solenoid2High: false,
            solenoid3High: false,
        }
    };

    const payloadString = JSON.stringify(payload);

    if (apiSocket.readyState === WebSocket.OPEN) {
        apiSocket.send(payloadString);
        console.log('Sent test JSON:', payloadString);
    } else {
        console.warn('WebSocket not open. ReadyState:', apiSocket.readyState);
    }
}
