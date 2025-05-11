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
var packetsAV1offset = 0;
var packetsGSE = 0;
var packetsGSEoffset = 0;

// API
const initialReconnectInterval = 200;
const maxReconnectInterval = 5000;
const graphRenderRate = 20; // fps for graphs (5 still looks good)

var apiSocket;
var apiTimestamp = 0; // Timestamp for keeping up with API
var displayTimestamp = 0; // Timestamp rendered to display and used for graphs
var reconnectInterval = initialReconnectInterval;
var reconnectTimeout;
var connected = false;
var then, now, fpsInterval;

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
        // This will be overwritten by API time when packets come through again
        apiTimestamp += (elapsed/1000);
        displayTimestamp = Math.max(displayTimestamp, apiTimestamp - (fpsInterval/1000));

        // Update timestamps to current time
        if (displayTimestamp - apiTimestamp > 0.5) {
            displayTimestamp = apiTimestamp;
        }

        // Log time
        //console.log(apiTimestamp, displayTimestamp, fpsInterval/1000);
    }
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
    apiSocket = new WebSocket(`ws://${api_url}:1887`);

    apiSocket.onopen = () => {
        connected = true;
        console.log(`Successfully connected to server at: - ${api_url}`);
        logMessage("Connected successfully", "notification");
        clearTimeout(reconnectTimeout);
        reconnectInterval = initialReconnectInterval;
    };

    apiSocket.onmessage = API_OnMessage;

    apiSocket.onerror = (error) => {
        connected = false;
        console.error("websocket error: ", error);
    };

    apiSocket.onclose = () => {
        connected = false;
        console.log("Socket closed: attempting to reconnect automatically");
        logMessage("Connection Lost: Attempting to reconnect", "error");
        scheduleReconnect();
    };
}
API_socketConnect();

function API_OnMessage(event) {
    let apiLatest, apiData;
    try {
        apiLatest = JSON.parse(event.data);
        //console.log(apiLatest);

        // Basic data processing
        apiData = processDataForDisplay(apiLatest.data, apiLatest.id);

        // Check for errors
        checkErrorConditions(apiData);

        // HANDLE SINGLE OPERATOR PACKETS
        if ([2].includes(apiData.id)) {

        }
        // HANDLE AVIONICS PACKETS
        else if ([3, 4, 5].includes(apiData.id)) {
            // AV DISPLAY VALUES
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

            // AV GRAPHS
            if (typeof graphUpdateAvionics === "function") {
                graphUpdateAvionics(apiData);
            }
            if (typeof graphUpdatePosition === "function") {
                graphUpdatePosition(apiData);
            }

            // AV ROCKET
            // Rocket module
            if (apiData.id == 4) {
                if (typeof rocketUpdate === "function") {
                    rocketUpdate(apiData);
                }
            }
        }
        // HANDLE GSE PACKETS
        else if ([6, 7].includes(apiData.id)) {
            // GSE DISPLAY VALUES
            // Radio module
            if (typeof displayUpdateRadio === 'function') {
                displayUpdateRadio(apiData);
            }

            // Auxilliary data module
            if (typeof displayUpdateAuxData === 'function') {
                displayUpdateAuxData(apiData);
            }

            // GSE GRAPHS
            if (typeof graphUpdateAuxData === "function") {
                graphUpdateAuxData(apiData);
            }
        }

    } catch (error) {
        console.error("Data processing error:", error);
    }
}

function checkErrorConditions(apiData) {
    if (apiData.errorFlags != undefined) {
        Object.entries(apiData.errorFlags).forEach(([key, value]) => {
            if (value === true) {
                logMessage(`${key} flag raised`, "error");
            }
        });
    }
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

    if (apiData?.meta) {
        // Timestamp and connection
        if (apiData.meta?.timestampS) {
            apiTimestamp = apiData.meta.timestampS;
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
