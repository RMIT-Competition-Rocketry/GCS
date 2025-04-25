const CHART_ALT = {
    selector: "#altitude",
    margin: { top: 20, right: 20, bottom: 30, left: 50 },
    width: 600,
    height: 400,
    xlabel: "Altitude",
};

const CHART_ALT_STATIC = {
    selector: "#altitude-static",
    margin: { top: 10, right: 10, bottom: 20, left: 40 },
    width: 600,
    height: 150,
    xlabel: "Altitude",
};

function dataLineGraph(chart) {
    // Create and initialise a graph
    chart.svg = d3.select(chart.selector);

    // Update graph margins and axes
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
    chart.g
        .selectAll(".tick line")
        .attr("stroke", "#f79322");

    chart.yAxis = chart.g.append("g").attr("class", "y-axis");
    chart.yAxis
        .call(d3.axisLeft(chart.y))
        .selectAll(".domain")
        .attr("stroke", "#f79322")
        .attr("stroke-width", 2);
    chart.yAxis
        .selectAll(".tick line") 
        .attr("stroke", "#f79322");

    // Line
    chart.line = d3
        .line()
        .x((d, i) => chart.x(i))
        .y((d) => chart.y(d));
    chart.path = chart.g
        .append("path")
        .datum(d3.range(50).map(() => 0)) // initial data
        .attr("fill", "none")
        .attr("stroke", "red")
        .attr("stroke-width", 1.5)
        .attr("d", chart.line);
}

// Load all data at once
function renderCSV(csvData) {
    CHART_ALT_STATIC.x.domain([0, csvData.length - 1]);
    CHART_ALT_STATIC.y.domain([d3.min(csvData) - 5, d3.max(csvData) + 5]);

    CHART_ALT_STATIC.g
        .select("g")
        .transition()
        .duration(0)
        .call(d3.axisBottom(CHART_ALT_STATIC.x));
    CHART_ALT_STATIC.yAxis
        .transition()
        .duration(0)
        .call(d3.axisLeft(CHART_ALT_STATIC.y));

    CHART_ALT_STATIC.path.datum(csvData).attr(
        "d",
        CHART_ALT_STATIC.line.x((d, i) => CHART_ALT_STATIC.x(i))
    );
}

// Progressively load CSV data (like simulation)
function simulateCSV(csvData) {
    // Initialise loop
    let index = 0;
    let data = [];

    d3.interval(() => {
        if (index < csvData.length) {
            // Add new value to data
            data.push(csvData[index]);
            // console.log(csvData[index]);

            // Update X domain dynamically
            x.domain([0, data.length - 1]);
            g.select("g").transition().duration(0).call(d3.axisBottom(x));

            // Update Y domain dynamically
            const yMin = d3.min(data);
            const yMax = d3.max(data);
            y.domain([yMin - 5, yMax + 5]); // add padding
            yAxis.transition().duration(0).call(d3.axisLeft(y));

            path.datum(data).attr(
                "d",
                line.x((d, i) => x(i))
            );

            // Increment index
            index++;
        }
    }, 20);
}

window.addEventListener("load", function () {
    // Build D3 chart
    dataLineGraph(CHART_ALT);
    dataLineGraph(CHART_ALT_STATIC);

    // Load data from CSV
    d3.csv("data/testData2.csv", (d) => +d.Altitude).then((csvData) => {
        renderCSV(csvData);
        //simulateCSV(csvData);
    });
});
