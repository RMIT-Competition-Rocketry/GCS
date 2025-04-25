const margin = { top: 20, right: 20, bottom: 40, left: 50 };
const width = 600;
const height = 400;

const graphWidth = width - margin.left - margin.right;
const graphHeight = height - margin.top - margin.bottom;

const svg = d3
    .select("#altitude")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// 👇 This group is shifted to make space for axes
const chart = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

d3.csv("/data/testData2.csv", d3.autoType).then(function (data) {
    // Set up scales
    const y = d3
        .scaleLinear()
        .range([graphHeight, 0]) // flip because SVG origin is top-left
        .domain([0, d3.max(data, (d) => d.Altitude)]);

    const x = d3
        .scaleLinear()
        .range([0, graphWidth])
        .domain(d3.extent(data, (d) => d.Flight_Time));

    // Draw axes ONCE
    chart
        .append("g")
        .attr("transform", `translate(0, ${graphHeight})`) // x axis at bottom
        .call(d3.axisBottom(x));

    chart.append("g").call(d3.axisLeft(y));

    // Define line generator
    const line = d3
        .line()
        .x((d) => x(d.Flight_Time))
        .y((d) => y(d.Altitude));

    function drawLine() {
        const path = chart
            .selectAll(".line-path")
            .data([data])
            .join("path")
            .attr("class", "line-path")
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 2)
            .attr("d", line);

        const pathLength = path.node().getTotalLength();

        path.attr("stroke-dasharray", pathLength)
            .attr("stroke-dashoffset", pathLength)
            .transition()
            .duration(1000)
            .ease(d3.easeSin)
            .attr("stroke-dashoffset", 0);
    }

    // Initial draw
    drawLine();

    // Redraw every 1.5 seconds
    let index = 0;
    setInterval(() => {
        drawLine();
        index = (index + 1) % data.length;
    }, 1500);
});
