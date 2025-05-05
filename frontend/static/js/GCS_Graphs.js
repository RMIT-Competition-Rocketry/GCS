/**
 * GCS Data Visualiser
 *
 * Uses d3.js to plot data from the API in beautiful graphs
 *
 * Functions and constants should be prefixed with "graph_"
 */

MAX_POINTS = 200;

// DEFINE CHARTS
const LINE_COLOURS = [
    "var(--color-red-500)",
    "var(--color-green-500)",
    "var(--color-blue-500)",
    "white",
];
const DEFAULT_MARGINS = { top: 4, right: 10, bottom: 20, left: 40 };

const GRAPH_AV_ACCEL = {
    selector: "#graph-av-accel",
    data: [],
    ylabel: "Acceleration (g)",
};
const GRAPH_AV_GYRO = { selector: "#graph-av-gyro", data: [], ylabel: "Rotation Rate (°/s)" };
const GRAPH_AV_VELOCITY = {
    selector: "#graph-av-velocity",
    data: [],
    margin: { top: 8, right: 8, bottom: 20, left: 50 },
    ylabel: "Vertical Speed (m/s)",
};
const GRAPH_POS_ALT = {
    selector: "#graph-pos-alt",
    data: [],
    margin: { top: 8, right: 8, bottom: 20, left: 50 }, ylabel: "Altitude (ft)",
};
const GRAPH_AUX_TRANSDUCERS = { selector: "#graph-aux-transducers", data: [], ylabel: "Pressure (bar)" };
const GRAPH_AUX_THERMOCOUPLES = {
    selector: "#graph-aux-thermocouples",
    data: [], ylabel: "Temperature (°C)"
};
const GRAPH_AUX_INTERNALTEMP = {
    selector: "#graph-aux-internaltemp",
    data: [], ylabel: "Temperature (°C)" 
};
const GRAPH_AUX_GASBOTTLES = { selector: "#graph-aux-gasbottles", data: [], ylabel: "Mass (kg)" };

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

    // Line
    /*
    chart.line = d3
        .line()
        .x((d, i) => chart.x(i))
        .y((d) => chart.y(d));
    chart.path = chart.g
        .append("path")
        .datum(d3.range(1).map(() => 0)) // initial data
        .attr("fill", "none")
        .attr("stroke", "red")
        .attr("stroke-width", 1.5)
        .attr("d", chart.line);
        */

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
        d3.axisLeft(chart.y).tickFormat((d) => (Number.isInteger(d) ? d : ""))
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
    if (chart != undefined && chart.x != undefined && chart.lines != undefined) {
        // Limit chart to MAX_POINTS (rolling)
        if (chart.xOffset === undefined) {
            chart.xOffset = 0; // Store the number of points shifted
        }

        let xShift = 0;
        chart.lines.forEach(line => {
            if (line.data.length > MAX_POINTS) {
                xShift = (line.data.length - MAX_POINTS);
                line.data.splice(0, line.data.length - MAX_POINTS); // Remove old points
            }
        });
        chart.xOffset += xShift;


        // Update X domain
        chart.x.domain([
            chart.xOffset,
            Math.max(...chart.lines.map((line) => line.data.length)) - 1 + chart.xOffset,
        ]);
        chart.g
            .select("g")
            .transition()
            .duration(0)
            .call(
                d3
                    .axisBottom(chart.x)
                    .tickFormat((d) => (Number.isInteger(d) ? d : ""))
            );

        // Update Y domain (with padding for multiple lines)
        const allData = chart.lines.flatMap((line) => line.data);
        chart.y.domain([d3.min(allData) - 1, d3.max(allData) + 1]).nice();
        chart.yAxis
            .transition()
            .duration(0)
            .call(
                d3
                    .axisLeft(chart.y)
                    .tickFormat((d) => (Number.isInteger(d) ? d : ""))
            );

        // De-emphasixe hidden non-integer axis values 
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

        // Remove old lines before rendering new ones
        chart.g.selectAll(".line-path").remove();

        // Render each line with a different color
        chart.lines.forEach((lineData, index) => {
            const line = d3
                .line()
                .x((d, i) => chart.x(i+chart.xOffset))
                .y((d) => chart.y(d));

            // Add path for each line
            chart.g
                .append("path")
                .datum(lineData.data)
                .attr("class", "line-path")
                .attr("fill", "none")
                .attr("stroke", lineData.color || LINE_COLOURS[index]) // Cycle through colors
                .attr("stroke-width", 1.5)
                .attr("d", line);
        });
    }
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

    // Load data from CSV
    /*
    d3.csv("data/testData2.csv", (d) => [+d.Altitude, +d.velocity, +d.TiltAngle, +d.FutureAngle, +d.RollAngle]).then(
        (csvData) => {
            graphFromCSVSimulated(csvData.map((item) => item[0]), GRAPH_POS_ALT);
            graphFromCSVSimulated(csvData.map((item) => item[1]), GRAPH_AV_VELOCITY);
            graphFromCSVSimulated(csvData.map((item) => item[2]), GRAPH_AV_GYRO);
            graphFromCSVSimulated(csvData.map((item) => item[3]), GRAPH_AV_ACCEL);
        }
    );*/
});

// Update modules
function graphUpdateAvionics(data) {
    // AVIONICS MODULE GRAPHS
    if (data.id == 3) {
        // Acceleration
        if (
            data.accelX != undefined &&
            data.accelY != undefined &&
            data.accelZ != undefined
        ) {
            if (GRAPH_AV_ACCEL.lines != undefined) {
                GRAPH_AV_ACCEL.lines[0].data.push(data.accelX);
                GRAPH_AV_ACCEL.lines[1].data.push(data.accelY);
                GRAPH_AV_ACCEL.lines[2].data.push(data.accelZ);
                graphRender(GRAPH_AV_ACCEL);
            }
        }

        // Gyroscope
        if (
            data.gyroX != undefined &&
            data.gyroY != undefined &&
            data.gyroZ != undefined
        ) {
            if (GRAPH_AV_GYRO.lines != undefined) {
                GRAPH_AV_GYRO.lines[0].data.push(data.gyroX);
                GRAPH_AV_GYRO.lines[1].data.push(data.gyroY);
                GRAPH_AV_GYRO.lines[2].data.push(data.gyroZ);
                graphRender(GRAPH_AV_GYRO);
            }
        }
    }

    // Velocity
    if (data.velocity != undefined) {
        if (GRAPH_AV_VELOCITY.lines != undefined) {
            GRAPH_AV_VELOCITY.lines[0].data.push(data.velocity);
            graphRender(GRAPH_AV_VELOCITY);
        }
    }
}

function graphUpdatePosition(data) {
    // POSITION MODULE GRAPHS
    // Altitude
    if (data.altitude != undefined) {
        if (GRAPH_POS_ALT.lines != undefined) {
            GRAPH_POS_ALT.lines[0].data.push(metresToFeet(data.altitude)); // Graph in feet
            graphRender(GRAPH_POS_ALT);
        }
    }
}

function graphUpdateAuxData(data) {
    // AUXILLIARY DATA MODULE GRAPHS
    if (data.id == 6) {
        // Transducers
        if (
            data.transducer1 != undefined &&
            data.transducer2 != undefined &&
            data.transducer3 != undefined
        ) {
            if (GRAPH_AUX_TRANSDUCERS.lines != undefined) {
                GRAPH_AUX_TRANSDUCERS.lines[0].data.push(data.transducer1);
                GRAPH_AUX_TRANSDUCERS.lines[1].data.push(data.transducer2);
                GRAPH_AUX_TRANSDUCERS.lines[2].data.push(data.transducer3);
                graphRender(GRAPH_AUX_TRANSDUCERS);
            }
        }

        // Thermocouples
        if (
            data.thermocouple1 != undefined &&
            data.thermocouple2 != undefined &&
            data.thermocouple3 != undefined &&
            data.thermocouple4 != undefined
        ) {
            if (GRAPH_AUX_THERMOCOUPLES.lines != undefined) {
                GRAPH_AUX_THERMOCOUPLES.lines[0].data.push(data.thermocouple1);
                GRAPH_AUX_THERMOCOUPLES.lines[1].data.push(data.thermocouple2);
                GRAPH_AUX_THERMOCOUPLES.lines[2].data.push(data.thermocouple3);
                GRAPH_AUX_THERMOCOUPLES.lines[3].data.push(data.thermocouple4);
                graphRender(GRAPH_AUX_THERMOCOUPLES);
            }
        }
    }

    if (data.id == 7) {
        // Internal temperature
        if (data.internalTemp != undefined) {
            if (GRAPH_AUX_INTERNALTEMP.lines != undefined) {
                GRAPH_AUX_INTERNALTEMP.lines[0].data.push(data.internalTemp);
                graphRender(GRAPH_AUX_INTERNALTEMP);
            }
        }

        // Gas bottle weights
        if (
            data.gasBottleWeight1 != undefined &&
            data.gasBottleWeight2 != undefined
        ) {
            if (GRAPH_AUX_GASBOTTLES.lines != undefined) {
                GRAPH_AUX_GASBOTTLES.lines[0].data.push(data.gasBottleWeight1);
                GRAPH_AUX_GASBOTTLES.lines[1].data.push(data.gasBottleWeight2);
                graphRender(GRAPH_AUX_GASBOTTLES);
            }
        }
    }
}
