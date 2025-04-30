/**
 * GCS Data Visualiser
 *
 * Uses d3.js to plot data from the API in beautiful graphs
 *
 * Functions and constants should be prefixed with "graph_"
 */

// DEFINE CHARTS
const DEFAULT_MARGINS = { top: 8, right: 8, bottom: 20, left: 40 };
const GRAPH_POS_ALT = { selector: "#graph-pos-alt", data:[] };
const GRAPH_AV_ACCEL = { selector: "#graph-av-accel", data:[] };
const GRAPH_AV_GYRO = { selector: "#graph-av-gyro", data:[] };
const GRAPH_AV_VELOCITY = { selector: "#graph-av-velocity", data:[] };

// Create and initialise line graphs
function graphCreateLine(chart) {
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
    chart.g
        .append("g")
        .attr("transform", `translate(0,${chart.graphHeight})`)
        .call(d3.axisBottom(chart.x))
        .selectAll(".domain")
        .attr("stroke", "#f79322")
        .attr("stroke-width", 2);
    chart.g.selectAll(".tick line").attr("stroke", "#f79322");

    chart.yAxis = chart.g.append("g").attr("class", "y-axis");
    chart.yAxis
        .call(d3.axisLeft(chart.y))
        .selectAll(".domain")
        .attr("stroke", "#f79322")
        .attr("stroke-width", 2);
    chart.yAxis.selectAll(".tick line").attr("stroke", "#f79322");

    // Line
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
    chart.g.select("g")
        .attr("transform", `translate(0,${chart.graphHeight})`)
        .call(d3.axisBottom(chart.x));

    chart.y.range([chart.graphHeight, 0]);
    chart.yAxis.call(d3.axisLeft(chart.y));

    // Re-render
    graphRender(chart);
}

// Render graph
function graphRender(chart) {
    if (chart != undefined && chart.x != undefined) {
        // Update X domain
        chart.x.domain([0, chart.data.length - 1]);
        chart.g.select("g").transition().duration(0).call(d3.axisBottom(chart.x));

        // Update Y domain
        chart.y.domain([d3.min(chart.data) - 1, d3.max(chart.data) + 1]);
        chart.yAxis.transition().duration(0).call(d3.axisLeft(chart.y));

        // Draw line on graph
        chart.path.datum(chart.data).attr(
            "d",
            chart.line.x((d, i) => chart.x(i))
        );
    }
}

window.addEventListener("load", function () {
    // Build D3 chart
    graphCreateLine(GRAPH_POS_ALT);
    graphCreateLine(GRAPH_AV_ACCEL);
    graphCreateLine(GRAPH_AV_GYRO);
    graphCreateLine(GRAPH_AV_VELOCITY);

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
    if (data.accelX != undefined || data.accelY != undefined || data.accelZ != undefined) {
        if (data.accelX != undefined) {
            GRAPH_AV_ACCEL.data.push(data.accelX);
        }
        graphRender(GRAPH_AV_ACCEL);
    }

    if (data.gyroX != undefined || data.gyroY != undefined || data.gyroZ != undefined) {
        if (data.gyroX != undefined) {
            GRAPH_AV_GYRO.data.push(data.gyroX);
        }
        graphRender(GRAPH_AV_GYRO);
    }

    if (data.velocity != undefined) {
        GRAPH_AV_VELOCITY.data.push(data.velocity);
        graphRender(GRAPH_AV_VELOCITY);
    }
}

function graphUpdatePosition(data) {
    if (data.altitude != undefined) {
        GRAPH_POS_ALT.data.push(data.altitude);
        graphRender(GRAPH_POS_ALT);
    }
}