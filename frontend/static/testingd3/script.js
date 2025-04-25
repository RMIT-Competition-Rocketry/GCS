// Set up the SVG canvas dimensions
const width = 600;
const height = 400;

// Create the SVG element
const svg = d3.select("svg").attr("width", width).attr("height", height);

// Set up margins and inner dimensions for the graph
const margin = { top: 20, right: 20, bottom: 40, left: 50 };
const graphWidth = width - margin.left - margin.right;
const graphHeight = height - margin.top - margin.bottom;

// Create a group element inside SVG to hold the graph
const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

// Set up scales for x and y axes
const x = d3.scaleBand().range([0, graphWidth]).padding(0.1);

const y = d3.scaleLinear().range([graphHeight, 0]);

// Load the data from the CSV file
d3.csv("/data/testData2.csv").then((data) => {
    // Convert the data values to numbers
    data.forEach((d) => {
        d.Altitude = +d.Altitude;
    });

    // Set the domains for x and y scales
    x.domain(data.map((d) => d.Time)); // No changes here, we'll still use x for spacing
    y.domain([0, d3.max(data, (d) => d.Altitude)]);

    // Create the y-axis
    g.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(y))
        .selectAll(".tick text")
        .attr("class", "axis-label");

    // Create the bars initially with zero height
    const bars = g
        .selectAll(".bar")
        .data(data)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", (d) => x(d.Time)) // Position based on the x scale (no axis displayed)
        .attr("y", graphHeight) // Start the bars at the bottom (height = 0)
        .attr("width", x.bandwidth()) // Width based on x scale
        .attr("height", 0) // Start with no height (0)
        .transition()
        .duration(10000) // Animate over 1 second
        .attr("y", (d) => y(d.Altitude)) // Move the bar up
        .attr("height", (d) => graphHeight - y(d.Altitude)); // Set the height of the bar
});
