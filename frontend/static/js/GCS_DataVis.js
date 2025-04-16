/**
 * GCS Data Visualiser
 *
 * Uses d3.js to plot data from the API in beautiful graphs
 *
 * Functions and constants should be prefixed with "data_"
 */

// Define chart parameters
const DATA_CHART_ALT = {
    selector: "#altitude",
    margin: { top: 20, right: 20, bottom: 40, left: 50 },
    width: 100,
    height: 200,
    xlabel: "Altitude (feet)",
};

const DATA_CHART_VEL = {
    selector: "#velocity-graph",
    margin: { top: 20, right: 20, bottom: 40, left: 50 },
    width: 800,
    height: 400,
    xlabel: "Velocity (ft/s)",
};

function data_graphCreate(chart) {
    /// Create and initialise a graph
    // Update graph margins
    chart.graphWidth = chart.width - chart.margin.left - chart.margin.right;
    chart.graphHeight = chart.height - chart.margin.top - chart.margin.bottom;

    // Create SVG
    chart.svg = d3
        .select(chart.selector)
        .attr("width", chart.width)
        .attr("height", chart.height);
    chart.svg
        .append("text")
        .attr("class", "x label")
        .attr("text-anchor", "end")
        .attr("x", chart.width)
        .attr("y", chart.height - 6)
        .text(chart.xlabel);

    // Axes
    chart.x = d3.scaleBand().range([0, chart.graphWidth]).padding(0.1);
    chart.y = d3.scaleLinear().range([chart.graphHeight, 0]);

    // Build graph
    chart.graph = chart.svg
        .append("g")
        .attr(
            "transform",
            `translate(${chart.margin.left},${chart.margin.top})`
        );
    chart.graph.append("g").attr("class", "y-axis").call(d3.axisLeft(chart.y));
}

function data_graphCreate_Bar(chart) {
    // Create generic graph
    data_graphCreate(chart);

    // Make graph into a bar chart, initially with zero height
    chart.bar = chart.graph
        .append("rect")
        .attr("class", "bar")
        .attr("x", chart.x(0)) // The bar will be placed at the x position 0
        .attr("y", chart.graphHeight) // Start at the bottom (height = 0)
        .attr("width", chart.x.bandwidth()) // Width based on the x scale
        .attr("height", 0); // Initially, height = 0
}

window.addEventListener("load", function () {
    // Initialise graphs on page
    data_graphCreate_Bar(DATA_CHART_ALT);
    data_graphCreate_Bar(DATA_CHART_VEL);

    // Load the CSV data
    d3.csv("data/testData.csv", d3.autoType).then(function (data) {
        // Set initial domain for x and y scales
        DATA_CHART_ALT.x.domain([0]); //0 for animation purposes/one bar graph
        DATA_CHART_ALT.y.domain([0, d3.max(data, (d) => d.Baro_Altitude_AGL)]);
        //DATA_CHART_ALT.graph.attr("class", "y-axis").call(d3.axisLeft(DATA_CHART_ALT.y)); // Update y axis

        DATA_CHART_VEL.x.domain([0]);
        DATA_CHART_VEL.y.domain([
            d3.min(data, (d) => d.Velocity_Up),
            d3.max(data, (d) => d.Velocity_Up),
        ]);

        // Function to animate the bar with different data values
        function animateBar(index) {
            const currentData = data[index];
            // Update the bar's y position and height
            DATA_CHART_ALT.bar
                .transition()
                .duration(1) // Transition duration
                .ease(d3.easeCubicInOut) // Smooth easing function
                .attr("y", DATA_CHART_ALT.y(currentData.Baro_Altitude_AGL)) // Set the new y position based on the value
                .attr(
                    "height",
                    DATA_CHART_ALT.graphHeight -
                        DATA_CHART_ALT.y(currentData.Baro_Altitude_AGL)
                ); // Set the new height based on the value

            DATA_CHART_VEL.bar
                .transition()
                .duration(1) // Transition duration
                .ease(d3.easeCubicInOut) // Smooth easing function
                .attr("y", DATA_CHART_VEL.y(currentData.Velocity_Up))
                .attr(
                    "height",
                    DATA_CHART_VEL.graphHeight -
                        DATA_CHART_VEL.y(currentData.Velocity_Up)
                );
        }

        let index = 0;
        max_Baro_Altitude_AGL = 0;
        max_alt_m = 0;
        // Set an interval to cycle through the data every 0.02 seconds
        setInterval(function () {
            // Animate graphs
            animateBar(index);

            //Updates the html value
            const current = data[index];
            if (current) {
                interface_updateValue("av-alt-ft", current.Baro_Altitude_AGL);
                if (current.Baro_Altitude_AGL > max_Baro_Altitude_AGL) {
                    max_Baro_Altitude_AGL = current.Baro_Altitude_AGL;
                }
                var alt_metres = current.Baro_Altitude_AGL *0.3048;
                interface_updateValue("av-alt-m",alt_metres)
                if (alt_metres > max_alt_m) {
                    max_alt_m = alt_metres;
                }
                var velocity_metres = current.Velocity_Up * 0.3048;
                interface_updateValue("av-vel-v",velocity_metres.toFixed(4))
                interface_updateValue("av-maxalt-ft", max_Baro_Altitude_AGL);
                interface_updateValue("av-maxalt-m", max_alt_m);
            }

            // Update the index to the next data point, and reset to 0 when it exceeds the data length
            index = (index + 1) % data.length;
        }, 19); // Cycle every .02 seconds
    });
});
