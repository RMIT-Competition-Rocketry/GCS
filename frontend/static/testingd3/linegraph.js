const svg = d3.select("svg");
const width = +svg.attr("width");
const height = +svg.attr("height");
const margin = { top: 20, right: 20, bottom: 30, left: 50 };

const chartWidth = width - margin.left - margin.right;
const chartHeight = height - margin.top - margin.bottom;

const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear().domain([0, 199]).range([0, chartWidth]);
const y = d3.scaleLinear().domain([0, 5000]).range([chartHeight, 0]); // will only be used for non scaled

const line = d3
    .line()
    .x((d, i) => x(i))
    .y((d) => y(d));

const path = g
    .append("path")
    .datum(d3.range(50).map(() => 0)) // initial data
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1.5)
    .attr("d", line);

g.append("g")
    .attr("transform", `translate(0,${chartHeight})`)
    .call(d3.axisBottom(x));
//note this keeps original not scaling
// g.append("g").call(d3.axisLeft(y));

const maxLength = 200;
// Load data from CSV
d3.csv("data/testData2.csv", (d) => +d.Altitude).then((csvData) => {
    let index = 0;
    let data = d3.range(199).map(() => 0); // start with flat data/0
    const yAxis = g.append("g").attr("class", "y-axis");

    d3.interval(() => {
        if (index < csvData.length) {
            console.log(csvData[index]);
            data.push(csvData[index]); // add new value
            if (data.length > maxLength) data.shift();

            // Update Y domain to fit the last 200 values
            const yMin = d3.min(data);
            const yMax = d3.max(data);
            y.domain([yMin - 5, yMax + 5]); // add padding

            // Update Y axis (you can .transition() for animation)
            // duration can be changed for less jaring drop offs
            yAxis.transition().duration(0).call(d3.axisLeft(y));

            path.datum(data).attr("d", line);
            index++;
        }
    }, 20);
});
