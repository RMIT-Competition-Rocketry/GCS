// Set up the SVG canvas dimensions
const width = 100;
const height = 400;

// for next graph
const linewidth = 800;
const lineheight = 400;

// Create the SVG element
const svg = d3.select("#altitude").attr("width", width).attr("height", height);

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

//will be tested for line graphs later
// d3.csv("testdata.csv").then(function(data){
//   data.forEach(function(d,i){
//     d.index = i;
//     d.velocity = +d.velocity
//   });
//   //scales x and y using data length cause time weird
//   const xscale =d3Linear()
//     .domain([0,data.length-1])
//     .range([linewidth])

//   const yscale =d3.scaleLinear()
//     .domain([d3.min(data, d=> d.velocity),d3.max(data, d=> d.velocity)])
//     .range([lineheight,0])

//   svg1.append("g")
//     .attr("transform","translate(0" + lineheight+")")
//     .call(d3.axisbottom(xscale))

//   svg1.append("g")
//      .call(d3.axisLeft(yscale))

//   const line =d3.line()
//     .x(d=>xscale(d.index))
//     .y(d=>yscale(d.velocity))

//   svg1.append("path")
//     .data([data])
//     .attr("class","line")
//     .attr("d",line)
//     .style("fill","none")
//     .style("stroke","steelblue")
//     .style("stroke-width",2)

// });

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
// //mouse over feature test
// const tooltip =d3.select(".tooltip");

// Load the CSV data
d3.csv("/data/testData2.csv", d3.autoType).then(function (data) {
    // Set initial domain for x and y scales
    x.domain([0]); //0 for animation purposes/one bar graph
    y.domain([0, d3.max(data, (d) => d.Altitude)]);
    x1.domain([0]);
    y2.domain([
        d3.min(data, (d) => d.velocity),
        d3.max(data, (d) => d.velocity),
    ]);

    // const xScale = d3.scaleLinear()
    //    .domain([d3.min(data, d =>d.Time), d3.max(data, d => d.Time)])
    //    .range([margin.left, linewidth - margin.right]);

    // const yScaleVelocity = d3.scaleLinear()
    //   .domain([d3.min(data,d=>d.velocity), d3.max(data, d => d.velocity)])  // Map velocity (y-axis)
    //   .range([lineheight - margin.bottom, margin.top]);

    //   const line = d3.line()
    //     .x(d => xScale(d.Time))
    //     .y(d => yScaleVelocity(d.velocity));
    // //x axis
    //   svg1.append("g")
    //      .attr("class", "x-axis")
    //      .attr("transform", `translate(0,${height - margin.bottom})`)
    //     .call(d3.axisBottom(xScale));
    // //y axis
    //   svg1.append("g")
    //      .attr("class", "y-axis-velocity")
    //      .attr("transform", `translate(${margin.left}, 0)`)
    //      .call(d3.axisLeft(yScaleVelocity));

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
            .attr("y", y2(currentData.velocity))
            .attr("height", velocityHeight - y2(currentData.velocity));

        // Update the bar's y position and height
        bar.transition()
            .duration(1) // Transition duration
            .ease(d3.easeCubicInOut) // Smooth easing function
            .attr("y", y(currentData.Altitude)) // Set the new y position based on the value
            .attr("height", graphHeight - y(currentData.Altitude)); // Set the new height based on the value

        // non functional test
        // bar2.on("mouseover",function(event,d){
        //     tooltip.style("visibility","visible")
        //        .text(`altitude: ${d.velocity}`);
        //  })
        //  .on("mousemove",function(event){
        //     tooltip.style("top",(event.pageY +5)+"px")
        //        .style("left",(event.pageX +5)+ "px")
        //  })
        //  .on("mouseout",function(){
        //    tooltip.style("visbility","hidden")
        //  });
    }
    //need testing for animation
    // function animateline(index){
    //   const currentData = data[index];
    //   path
    //       .datum(data)
    //       .transition(1)
    //       .duration(1)
    //       .attr("d", line);
    // }

    // Index to track the current data point
    let index = 0;

    // Set an interval to cycle through the data every 2 seconds
    setInterval(function () {
        animateBar(index);

        // Update the index to the next data point, and reset to 0 when it exceeds the data length
        index = (index + 1) % data.length;
    }, 19); // Cycle every 2 seconds
});
