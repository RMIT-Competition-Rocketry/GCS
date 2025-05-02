const CHART_ALT = {
    selector: "#altitude",
    margin: { top: 10, right: 10, bottom: 20, left: 40 },
    width: 600,
    height: 200,
};

const CHART_ALT_STATIC = {
    selector: "#altitude-static",
    margin: { top: 10, right: 10, bottom: 20, left: 40 },
    width: 600,
    height: 200,
};

const CHART_VEL = {
    selector: "#velocity",
    margin: { top: 10, right: 10, bottom: 20, left: 40 },
    width: 600,
    height: 200,
};

const CHART_VEL_STATIC = {
    selector: "#velocity-static",
    margin: { top: 10, right: 10, bottom: 20, left: 40 },
    width: 600,
    height: 200,
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
}

// Load all data at once
function renderCSV(csvData, chart, n) {
    chart.x.domain([0, csvData.length - 1]);
    chart.y.domain([d3.min(csvData) - 5, d3.max(csvData) + 5]);

    chart.g.select("g").transition().duration(0).call(d3.axisBottom(chart.x));
    chart.yAxis.transition().duration(0).call(d3.axisLeft(chart.y));

    chart.path.datum(csvData).attr(
        "d",
        chart.line.x((d, i) => chart.x(i))
    );
}

// Progressively load CSV data (like simulation)
function simulateCSV(csvData, chart, n) {
    // Initialise loop
    let index = 0;
    let data = [];

    d3.interval(() => {
        if (index < csvData.length) {
            // Add new value to data
            data.push(csvData[index]);
            // console.log(csvData[index]);

            // Update X domain dynamically
            chart.x.domain([0, data.length - 1]);
            chart.g
                .select("g")
                .transition()
                .duration(0)
                .call(d3.axisBottom(chart.x));

            // Update Y domain dynamically
            let yMin = d3.min(data),
                yMax = d3.max(data);
            chart.y.domain([yMin - 5, yMax + 5]); // add padding
            chart.yAxis.transition().duration(0).call(d3.axisLeft(chart.y));

            chart.path.datum(data).attr(
                "d",
                chart.line.x((d, i) => chart.x(i))
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
    dataLineGraph(CHART_VEL);
    dataLineGraph(CHART_VEL_STATIC);

    // Load data from CSV
    d3.csv("data/testData2.csv", (d) => [+d.Altitude, +d.velocity]).then(
        (csvData) => {
            let altitudeData = csvData.map(item => item[0]);
            renderCSV(altitudeData, CHART_ALT_STATIC);
            simulateCSV(altitudeData, CHART_ALT);

            let velocityData = csvData.map(item => item[1]);
            renderCSV(velocityData, CHART_VEL_STATIC);
            simulateCSV(velocityData, CHART_VEL);
        }
    );
});
