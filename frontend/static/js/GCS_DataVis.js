/**
 * GCS Data Visualiser
 * 
 * Uses d3.js to plot data from the API in beautiful graphs
 *
 * Functions and constants should be prefixed with "data_"
 */

window.addEventListener("load", function () {
    // needs changes for both size and naming coventions when referencing the data
    // Set up the SVG canvas dimensions
    const width = 100;
    const height = 200;

    // for next graph
    const linewidth = 800;
    const lineheight = 400;

    // Create the SVG element
    const svg = d3
        .select("#altitude")
        .attr("width", width)
        .attr("height", height);

    svg.append("text")
        .attr("class", "x label")
        .attr("text-anchor", "end")
        .attr("x", width)
        .attr("y", height - 6)
        .text("Altitude (feet)");

    const svg1 = d3
        .select("#velocity-graph")
        .attr("width", linewidth)
        .attr("height", lineheight);

    svg1.append("text")
        .attr("class", "x label")
        .attr("text-anchor", "end")
        .attr("x", width)
        .attr("y", height - 6)
        .text("velocity(ft/s)");

    // Set up margins and inner dimensions for the graph
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const graphWidth = width - margin.left - margin.right;
    const graphHeight = height - margin.top - margin.bottom;

    const velocityWidth = linewidth - margin.left - margin.right;
    const velocityHeight = lineheight - margin.top - margin.bottom;

    // Create a group element inside SVG to hold the graph
    const g = svg
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const v = svg1
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
    // Set up scales for x and y axes
    const x = d3.scaleBand().range([0, graphWidth]).padding(0.1);

    const y = d3.scaleLinear().range([graphHeight, 0]);

    const x1 = d3.scaleBand().range([0, graphWidth]).padding(0.1);

    const y2 = d3.scaleLinear().range([graphHeight, 0]);

    // Load the CSV data
    d3.csv("data/testData.csv", d3.autoType).then(function (data) {
        // Set initial domain for x and y scales
        x.domain([0]); //0 for animation purposes/one bar graph
        y.domain([0, d3.max(data, (d) => d.Baro_Altitude_AGL)]);
        x1.domain([0]);
        y2.domain([
            d3.min(data, (d) => d.Velocity_Up),
            d3.max(data, (d) => d.Velocity_Up),
        ]);

        //for bar animation
        // Create the y-axis
        v.append("g").attr("class", "y-axis").call(d3.axisLeft(y2));
        g.append("g").attr("class", "y-axis").call(d3.axisLeft(y));

        // Create the bar initially with zero height
        const bar = g
            .append("rect")
            .attr("class", "bar")
            .attr("x", x(0)) // The bar will be placed at the x position 0
            .attr("y", graphHeight) // Start at the bottom (height = 0)
            .attr("width", x.bandwidth()) // Width based on the x scale
            .attr("height", 0); // Initially, height = 0

        // Create the bar initially with zero height
        const bar2 = v
            .append("rect")
            .attr("class", "bar2")
            .attr("x", x1(0))
            .attr("y", velocityHeight)
            .attr("width", x1.bandwidth())
            .attr("height", 0);

        // Function to animate the bar with different data values
        function animateBar(index) {
            const currentData = data[index];
            bar2.transition()
                .duration(1) // Transition duration
                .ease(d3.easeCubicInOut) // Smooth easing function
                .attr("y", y2(currentData.Velocity_Up))
                .attr("height", velocityHeight - y2(currentData.Velocity_Up));

            // Update the bar's y position and height
            bar.transition()
                .duration(1) // Transition duration
                .ease(d3.easeCubicInOut) // Smooth easing function
                .attr("y", y(currentData.Baro_Altitude_AGL)) // Set the new y position based on the value
                .attr("height", graphHeight - y(currentData.Baro_Altitude_AGL)); // Set the new height based on the value
        }

        let index = 0;

        // Set an interval to cycle through the data every 0.02 seconds
        setInterval(function () {
            animateBar(index);

            // Update the index to the next data point, and reset to 0 when it exceeds the data length
            index = (index + 1) % data.length;
        }, 19); // Cycle every .02 seconds
    });
});
