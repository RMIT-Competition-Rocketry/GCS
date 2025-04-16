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
};

const DATA_CHART_VEL = {
    selector: "#velocity-graph",
    margin: { top: 20, right: 20, bottom: 40, left: 50 },
    width: 800,
    height: 400,
};

function data_graphUpdateMargins(chart) {
    chart.graphWidth = chart.width - chart.margin.left - chart.margin.right;
    chart.graphHeight = chart.height - chart.margin.top - chart.margin.bottom;
}

function data_graphCreate_Altitude() {
    /// Create the altitude graph
    data_graphUpdateMargins(DATA_CHART_ALT);

    // Create SVG
    DATA_CHART_ALT.svg = d3
        .select(DATA_CHART_ALT.selector)
        .attr("width", DATA_CHART_ALT.width)
        .attr("height", DATA_CHART_ALT.height);
    DATA_CHART_ALT.svg
        .append("text")
        .attr("class", "x label")
        .attr("text-anchor", "end")
        .attr("x", DATA_CHART_ALT.width)
        .attr("y", DATA_CHART_ALT.height - 6)
        .text("Altitude (feet)");

    // Axes
    DATA_CHART_ALT.x = d3
        .scaleBand()
        .range([0, DATA_CHART_ALT.graphWidth])
        .padding(0.1);
    DATA_CHART_ALT.y = d3.scaleLinear().range([DATA_CHART_ALT.graphHeight, 0]);

    // Build graph
    DATA_CHART_ALT.graph = DATA_CHART_ALT.svg
        .append("g")
        .attr(
            "transform",
            `translate(${DATA_CHART_ALT.margin.left},${DATA_CHART_ALT.margin.top})`
        );
    DATA_CHART_ALT.graph
        .append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(DATA_CHART_ALT.y));
}

function data_graphCreate_Velocity() {
    /// Create the velocity graph
    data_graphUpdateMargins(DATA_CHART_VEL);

    // Create SVG
    DATA_CHART_VEL.svg = d3
        .select(DATA_CHART_VEL.selector)
        .attr("width", DATA_CHART_VEL.width)
        .attr("height", DATA_CHART_VEL.height);
    DATA_CHART_VEL.svg
        .append("text")
        .attr("class", "x label")
        .attr("text-anchor", "end")
        .attr("x", DATA_CHART_VEL.width)
        .attr("y", DATA_CHART_VEL.height - 6)
        .text("velocity(ft/s)");

    // Setup axes
    DATA_CHART_VEL.x = d3
        .scaleBand()
        .range([0, DATA_CHART_VEL.graphWidth])
        .padding(0.1);
    DATA_CHART_VEL.y = d3.scaleLinear().range([DATA_CHART_VEL.graphHeight, 0]);

    // Build graph
    DATA_CHART_VEL.graph = DATA_CHART_VEL.svg
        .append("g")
        .attr(
            "transform",
            `translate(${DATA_CHART_VEL.margin.left},${DATA_CHART_VEL.margin.top})`
        );
    DATA_CHART_VEL.graph
        .append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(DATA_CHART_VEL.y));
}

window.addEventListener("load", function () {
    // Initialise graphs on page
    data_graphCreate_Altitude();
    data_graphCreate_Velocity();

    // Load the CSV data
    d3.csv("data/testData.csv", d3.autoType).then(function (data) {
        // Set initial domain for x and y scales
        DATA_CHART_ALT.x.domain([0]); //0 for animation purposes/one bar graph
        DATA_CHART_ALT.y.domain([0, d3.max(data, (d) => d.Baro_Altitude_AGL)]);

        DATA_CHART_VEL.x.domain([0]);
        DATA_CHART_VEL.y.domain([
            d3.min(data, (d) => d.Velocity_Up),
            d3.max(data, (d) => d.Velocity_Up),
        ]);

        // Create the bar initially with zero height
        DATA_CHART_ALT.bar = DATA_CHART_ALT.graph
            .append("rect")
            .attr("class", "bar")
            .attr("x", DATA_CHART_ALT.x(0)) // The bar will be placed at the x position 0
            .attr("y", DATA_CHART_ALT.graphHeight) // Start at the bottom (height = 0)
            .attr("width", DATA_CHART_ALT.x.bandwidth()) // Width based on the x scale
            .attr("height", 0); // Initially, height = 0

        // Create the bar initially with zero height
        DATA_CHART_ALT.bar = DATA_CHART_VEL.graph
            .append("rect")
            .attr("class", "bar2")
            .attr("x", DATA_CHART_VEL.x(0))
            .attr("y", DATA_CHART_VEL.graphHeight)
            .attr("width", DATA_CHART_VEL.x.bandwidth())
            .attr("height", 0);

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

            DATA_CHART_ALT.bar
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
                interface_updateValue("av-maxalt-ft", max_Baro_Altitude_AGL);
            }

            // Update the index to the next data point, and reset to 0 when it exceeds the data length
            index = (index + 1) % data.length;
        }, 19); // Cycle every .02 seconds
    });
});
