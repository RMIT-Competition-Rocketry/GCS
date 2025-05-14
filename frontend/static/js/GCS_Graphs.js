/**
 * GCS Data Visualiser
 *
 * Uses d3.js to plot data from the API in beautiful graphs
 *
 * Functions and constants should be prefixed with "graph_"
 */

const MAX_TIME = 20; // Seconds of graph shown, TODO: load config
const GRAPH_GAP_SIZE = 1; // Amount of seconds between data points before a line isn't drawn between them
const GRAPH_TICKS_Y = 8;

// DEFINE CHARTS
const LINE_COLOURS = [
    "var(--color-red-500)",
    "var(--color-green-500)",
    "var(--color-blue-500)",
    "white",
];
const DEFAULT_MARGINS = { top: 6, right: 10, bottom: 24, left: 50 };

const GRAPH_AV_ACCEL = {
    selector: "#graph-av-accel",
    data: [],
    ylabel: "Acceleration (g)",
};
const GRAPH_AV_GYRO = {
    selector: "#graph-av-gyro",
    data: [],
    ylabel: "Rotation Rate (°/s)",
};
const GRAPH_AV_VELOCITY = {
    selector: "#graph-av-velocity",
    data: [],
    ylabel: "Vertical Speed (m/s)",
    limits: {
        yBottomMax: 0,
    },
};
const GRAPH_POS_ALT = {
    selector: "#graph-pos-alt",
    data: [],
    ylabel: "Altitude (ft)",
    limits: {
        yBottomMax: 0,
    },
};
const GRAPH_AUX_TRANSDUCERS = {
    selector: "#graph-aux-transducers",
    data: [],
    ylabel: "Pressure (bar)",
    limits: {
        yBottomMax: 0,
    },
};
const GRAPH_AUX_THERMOCOUPLES = {
    selector: "#graph-aux-thermocouples",
    data: [],
    ylabel: "Temperature (°C)",
    limits: {
        yBottomMax: 0,
    },
};
const GRAPH_AUX_INTERNALTEMP = {
    selector: "#graph-aux-internaltemp",
    data: [],
    ylabel: "Temperature (°C)",
    limits: {
        yBottomMax: 0,
    },
};
const GRAPH_AUX_GASBOTTLES = {
    selector: "#graph-aux-gasbottles",
    data: [],
    ylabel: "Mass (kg)",
};

const symbolCircle = d3.symbol()
    .type(d3.symbolCircle)
    .size(10);

// Create and initialise line graphs
function graphCreateLine(chart, numLines) {
    // Select SVG
    chart.svg = d3.select(chart.selector);

    // Dynamic graph size initialisation
    const boundingRect = chart.svg.node().parentElement.getBoundingClientRect();
    chart.width = boundingRect.width;
    chart.height = boundingRect.height;
    chart.svg
        .attr("viewBox", `0 0 ${chart.width} ${chart.height}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    // Update graph margins and axes
    if (chart.margin == undefined) {
        chart.margin = DEFAULT_MARGINS;
    }
    chart.graphWidth = chart.width - chart.margin.left - chart.margin.right;
    chart.graphHeight = chart.height - chart.margin.top - chart.margin.bottom;
    chart.x = d3.scaleLinear().range([0, chart.graphWidth]);
    chart.y = d3.scaleLinear().range([chart.graphHeight, 0]);

    // Build graph
    chart.g = chart.svg
        .append("g")
        .attr(
            "transform",
            `translate(${chart.margin.left},${chart.margin.top})`
        );

    // Create and style the x and y axis
    // x axis
    chart.g
        .append("g")
        .attr("transform", `translate(0,${chart.graphHeight})`)
        .call(
            d3
                .axisBottom(chart.x)
                .tickFormat((d) => (Number.isInteger(d) ? d : ""))
        )
        .selectAll(".domain")
        .attr("stroke", "#f79322")
        .attr("stroke-width", 2);
    chart.g.selectAll(".tick line").attr("stroke", "#f79322");

    // Y-axis
    chart.yAxis = chart.g.append("g").attr("class", "y-axis");
    chart.yAxis
        .call(
            d3
                .axisLeft(chart.y)
                .ticks(GRAPH_TICKS_Y)
                .tickFormat((d) => (Number.isInteger(d) ? d : ""))
        )
        .selectAll(".domain")
        .attr("stroke", "#f79322")
        .attr("stroke-width", 2);
    chart.yAxis.selectAll(".tick line").attr("stroke", "#f79322");

    // Y-axis Label
    chart.yAxisLabel = chart.svg
        .append("text")
        .attr("text-anchor", "middle")
        .attr("font-size", "90%")
        .attr("fill", "white")
        .attr("transform", "rotate(-90)")
        .attr("x", -Math.round(chart.graphHeight / 2))
        .attr("y", 10)
        .text(chart.ylabel || "Y LABEL");

    // Lines array to hold multiple line data sets
    chart.lines = [];
    for (let i = 0; i < numLines; i++) {
        chart.lines.push({ data: [], color: LINE_COLOURS[i] });
    }

    // ResizeObserver (for dynamic graph resizing)
    const resizeObserver = new ResizeObserver((entries) => {
        for (let entry of entries) {
            const { width, height } = entry.contentRect;
            chart.width = width;
            chart.height = height;
            graphResize(chart); // Call resize handler
        }
    });
    resizeObserver.observe(chart.svg.node().parentElement);
}

// Render static graph from CSV
function graphFromCSVStatic(csvData, chart) {
    chart.data = csvData;
    graphRender(chart);
}

// Simulate graph from CSV by progressively loading data
function graphFromCSVSimulated(csvData, chart) {
    // Initialise loop
    let index = 0;

    d3.interval(() => {
        if (index < csvData.length) {
            // Add new value to data
            chart.data.push(csvData[index]);

            // Render graph
            graphRender(chart);

            // Increment index
            index++;
        }
    }, 20);
}

// Resize graph
function graphResize(chart) {
    // Update SVG size
    chart.svg
        .attr("viewBox", `0 0 ${chart.width} ${chart.height}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    // Recalculate graph drawing area
    chart.graphWidth = chart.width - chart.margin.left - chart.margin.right;
    chart.graphHeight = chart.height - chart.margin.top - chart.margin.bottom;

    // Update axes
    chart.x.range([0, chart.graphWidth]);
    chart.g
        .select("g")
        .attr("transform", `translate(0,${chart.graphHeight})`)
        .call(
            d3
                .axisBottom(chart.x)
                .tickFormat((d) => (Number.isInteger(d) ? d : ""))
        );

    chart.y.range([chart.graphHeight, 0]);
    chart.yAxis.call(
        d3.axisLeft(chart.y).ticks(GRAPH_TICKS_Y).tickFormat((d) => (Number.isInteger(d) ? d : ""))
    );
    chart.yAxisLabel.attr(
        "x",
        -Math.round(chart.graphHeight / 2) - chart.margin.top
    );

    // Re-render
    graphRender(chart);
}

// Render graph
function graphRender(chart) {
    if (chart && chart?.x && chart?.lines) {
        // Get timestamp of data
        const now = Math.max(
            d3.max(chart.lines.flatMap(line => line.data), d => d.x),
            timestampLocal + timestampApiConnect - timeDrift);

        // Data is held in buffer for extra 5 seconds
        const windowStart = now - MAX_TIME;

        if (chart.lastRender != now) {
            chart.lastRender = now;

            // Limit data to window
            chart.lines.forEach(line => {
                // Data is held in buffer for extra 5 seconds in case there's timing issues
                line.data = line.data.filter(d => d.x >= (windowStart - GRAPH_GAP_SIZE - 5));
            });
            const allPoints = chart.lines.flatMap(line => line.data);
            
            // Update x and y domains
            chart.x.domain([windowStart, now]);
            chart.y.domain([
                Math.min(d3.min(allPoints, d => d.y) - 1, chart?.limits?.yBottomMax != undefined ? chart?.limits?.yBottomMax : Infinity),
                d3.max(allPoints, d => d.y) + 1
            ]);//.nice();

            // Update rendering of X and Y domain
            chart.g
                .select("g")
                .transition()
                .duration(0)
                .call(
                    d3.axisBottom(chart.x).tickFormat(d => `${d}`)
                );
            chart.yAxis
                .transition()
                .duration(0)
                .call(
                    d3
                        .axisLeft(chart.y)
                        .ticks(GRAPH_TICKS_Y)
                        .tickFormat((d) => (Number.isInteger(d) ? d : ""))
                );

            // De-emphasize hidden non-integer axis values 
            chart.g
                .selectAll(".tick")
                .filter((d) => !Number.isInteger(d))
                .select("line")
                .style("stroke", "#ccc")
                .style("stroke-width", 0.5);
            chart.g
                .selectAll(".tick")
                .filter((d) => !Number.isInteger(d))
                .select("text")
                .style("display", "none");

            // Remove old lines and dots before rendering new ones
            chart.g.selectAll(".line-path").remove();
            chart.g.selectAll(".line-dot").remove();

            // Render each line with a different color
            chart.lines.forEach((lineData, index) => {
                // Line rendering logic is a bit messy oops
                // If two points are close together, we draw a line between them.
                lineData.data.forEach((d, i, data) => {
                    d.prev = Math.abs(d.x - data[i-1]?.x) <= GRAPH_GAP_SIZE;
                    d.next = Math.abs(d.x - data[i+1]?.x) <= GRAPH_GAP_SIZE;

                    // If they're not close, we draw a point
                    if (d.x >= windowStart && d.x <= now) {
                        if (!d.prev && !d.next) {
                            chart.g.append("path")
                                .attr("class", "line-dot")
                                .attr("d", symbolCircle)
                                .attr("transform", `translate(${chart.x(d.x)},${chart.y(d.y)})`)
                                .attr("fill", lineData.color || LINE_COLOURS[index]);
                        } else if (!d.next || !d.prev) {
                            chart.g.append("path")
                                .attr("class", "line-dot")
                                .attr("d", symbolCircle) // Make cross?
                                .attr("transform", `translate(${chart.x(d.x)},${chart.y(d.y)})`)
                                .attr("fill", lineData.color || LINE_COLOURS[index]);
                        }
                    }
                    
                });

                // Add path for each line
                const line = d3
                    .line()
                    .x((d) => chart.x(d.x))
                    .y((d) => chart.y(d.y))
                    .defined((d, i, data) => {
                        return d.prev;//d.prev && d.next;
                    });

                chart.g
                    .append("path")
                    .datum(lineData.data.filter(d => d.x >= windowStart && d.x <= now))
                    .attr("class", "line-path")
                    .attr("fill", "none")
                    .attr("stroke", lineData.color || LINE_COLOURS[index]) // Cycle through colors
                    .attr("stroke-width", 1.5)
                    .attr("stroke-linecap", "round")
                    .attr("d", line);
            });
        }
    }
}

function graphRequestRender() {
    // Attempt to render all graphs
    graphRender(GRAPH_AV_ACCEL);
    graphRender(GRAPH_AV_GYRO);
    graphRender(GRAPH_AV_VELOCITY);

    graphRender(GRAPH_POS_ALT);

    graphRender(GRAPH_AUX_TRANSDUCERS);
    graphRender(GRAPH_AUX_THERMOCOUPLES);
    graphRender(GRAPH_AUX_INTERNALTEMP);
    graphRender(GRAPH_AUX_GASBOTTLES);
}

function graphAddValue(graph, line, timestamp, value) {
    // Adds a value to a graph in the right position
    // To make sure things are all valid and don't go out of order

    // Make sure graph is valid and has lines defined
    if (!graph?.lines || line < 0 || line >= graph.lines.length) return;

    // Ensure timestamp is a valid number
    if (timestamp == undefined || isNaN(timestamp) || timestamp < 0) return;

    // Ensure value is a number
    if (value == undefined || isNaN(value)) return;

    // Add data to graph (sorted in chronological order)
    const data = graph.lines[line].data;
    const point = {x: timestamp, y:value};

    // Loop backwards from the end to find where to insert the data
    let index = data.length;
    while (index > 0 && data[index - 1].x > timestamp) {
        index--;
    }
    data.splice(index, 0, point);

    //graph.lines[line].data.push({ x: timestamp, y: value});
}

window.addEventListener("DOMContentLoaded", function () {
    // Build D3 chart
    graphCreateLine(GRAPH_AV_ACCEL, 3);
    graphCreateLine(GRAPH_AV_GYRO, 3);
    graphCreateLine(GRAPH_AV_VELOCITY, 1);

    graphCreateLine(GRAPH_POS_ALT, 1);

    graphCreateLine(GRAPH_AUX_TRANSDUCERS, 3);
    graphCreateLine(GRAPH_AUX_THERMOCOUPLES, 4);
    graphCreateLine(GRAPH_AUX_INTERNALTEMP, 1);
    graphCreateLine(GRAPH_AUX_GASBOTTLES, 2);
});

// Update modules
function graphUpdateAvionics(data) {
    // AVIONICS MODULE GRAPHS
    if (data?.id && data?.meta?.timestampS && data?.meta?.totalPacketCountAv) {
        const timestamp = data.meta.timestampS;

        // Acceleration
        graphAddValue(GRAPH_AV_ACCEL, 0, timestamp, data.accelX);
        graphAddValue(GRAPH_AV_ACCEL, 1, timestamp, data.accelY);
        graphAddValue(GRAPH_AV_ACCEL, 2, timestamp, data.accelZ);

        // Gyroscope
        graphAddValue(GRAPH_AV_GYRO, 0, timestamp, data.gyroX);
        graphAddValue(GRAPH_AV_GYRO, 1, timestamp, data.gyroY);
        graphAddValue(GRAPH_AV_GYRO, 2, timestamp, data.gyroZ);

        // Velocity
        graphAddValue(GRAPH_AV_VELOCITY, 0, timestamp, data.velocity);
    }
}

function graphUpdatePosition(data) {
    // POSITION MODULE GRAPHS
    if (data?.id && data?.meta?.timestampS && data?.meta?.totalPacketCountAv) {
        const timestamp = data.meta.timestampS;

        // Altitude
        graphAddValue(GRAPH_POS_ALT, 0, timestamp, metresToFeet(data.altitude));
    }
}

function graphUpdateAuxData(data) {
    // AUXILLIARY DATA MODULE GRAPHS
    if (data?.id && data?.meta?.timestampS && data?.meta?.totalPacketCountGse) {
        const timestamp = data.meta.timestampS;

        // Transducers
        graphAddValue(GRAPH_AUX_TRANSDUCERS, 0, timestamp, data.transducer1);
        graphAddValue(GRAPH_AUX_TRANSDUCERS, 1, timestamp, data.transducer2);
        graphAddValue(GRAPH_AUX_TRANSDUCERS, 2, timestamp, data.transducer3);

        // Thermocouples
        graphAddValue(GRAPH_AUX_THERMOCOUPLES, 0, timestamp, data.thermocouple1);
        graphAddValue(GRAPH_AUX_THERMOCOUPLES, 1, timestamp, data.thermocouple2);
        graphAddValue(GRAPH_AUX_THERMOCOUPLES, 2, timestamp, data.thermocouple3);
        graphAddValue(GRAPH_AUX_THERMOCOUPLES, 3, timestamp, data.thermocouple4);

        // Internal temperature
        graphAddValue(GRAPH_AUX_INTERNALTEMP, 0, timestamp, data.internalTemp);

        // Gas bottle weights
        graphAddValue(GRAPH_AUX_GASBOTTLES, 0, timestamp, data.gasBottleWeight1);
        graphAddValue(GRAPH_AUX_GASBOTTLES, 1, timestamp, data.gasBottleWeight2);
    }
}
