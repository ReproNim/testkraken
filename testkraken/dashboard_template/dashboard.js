var parcoords;
var dataset;
var dataView;
var envs;


d3.csv("output_all.csv", function(data) {

    "use strict";

    data.forEach(function (d, i) {
        d.id = d.id || i;
    });

    dataset = data;

    console.log('data is', data);

    var colors = {
        "pass": "green",
        "fail": "red",
        "error": "gray"
    };

    function colorByResult(result) {
        return colors[result.toLowerCase()];
    }

    var hideaxis_list = []

    parcoords = d3.parcoords()("#parcoord-plot")
        .data(data)
        .alpha(0.5)
        .mode("queue")
        //.rate(30)
        .margin({ top: 30, left: 0, bottom: 20, right: 0 })
        .hideAxis(hideaxis_list)
        //.color(function (d) {return colorByResult(d.result); })
        .color("indigo")
        .render()
        .reorderable()
        .brushMode("1D-axes")
        .autoscale();


// creating table with results

    var columns = d3.keys(data[0])

  //function tabulate(data, columns) {
		var table = d3.select('#grid').append('table')
		var thead = table.append('thead')
		var	tbody = table.append('tbody');

		// append the header row
		thead.append('tr')
		  .selectAll('th')
		  .data(columns).enter()
		  .append('th')
		    .text(function (column) { return column; })
		    .style('background-color', '#5c1cab66')
		    .style('color', 'black')
		    .style("border", "2px solid #5c1cab")
		    .style("padding", "6px");

		// create a row for each object in the data
		var rows = tbody.selectAll('tr')
		  .data(data)
		  .enter()
		  .append('tr')
		  .style("background-color", function(d, i){
		    if ( i % 2) {
		        return 'white';
		    } else {
		        return '#bea4dd33';
		    }
		  })
		  .style("color", "black")
		  .style("border", "1px solid #5c1cab66")
		  .style("padding", "6px")
		  ;

		// create a cell in each row for each column
		var cells = rows.selectAll('td')
		  .data(function (row) {
		    return columns.map(function (column) {
		      return {column: column, value: row[column]};
		    });
		  })
		  .enter()
		  .append('td')
		    .text(function (d) { return d.value; })
		    .style("border", "2px solid #5c1cab")
		    .style("padding", "6px")
		    ;

	//  return table;
	//}

	// render the table(s)
	//tabulate(data, d3.keys(data[0]))
    //grid.append(tabulate(grid, data, d3.keys(data[0])));

    // TODO: not sure if I have to update everything as in this function
    function update(columns_new){
    table.selectAll('thead').selectAll("tr").selectAll("th")
          .data(columns_new)
      .enter()
      .append("th")

//    table.selectAll("th")
        .text(function(d, i){

          return d
        })
        .style('background-color', '#5c1cab66')
		 .style('color', 'black')
		 .style("border", "2px solid #5c1cab")
		 .style("padding", "6px");


    table.selectAll('thead').selectAll("tr").selectAll("th")
        .data(columns_new)
        .exit()
        .remove("th")


	table.selectAll('tbody').selectAll('tr')
		  .data(data)
		  .enter()
		  .append('tr')
		  .style("background-color", function(d, i){
		    if ( i % 2) {
		        return 'white';
		    } else {
		        return '#bea4dd33';
		    }
		  })
		  .style("color", "black")
		  .style("border", "1px solid #5c1cab")
		  .style("padding", "6px")
		  ;
    console.log("data(columns_new)", data);

    table.selectAll('tbody').selectAll("tr")
      .data(data)
      .exit()
      .remove("tr")


    table.selectAll('tbody').selectAll('tr').selectAll("td")
      .data(columns_new)
      .enter()
      .append("td")


    table.selectAll('tbody').selectAll('tr').selectAll("td")
		  .data(function (row) {
		    return columns_new.map(function (column) {
		      //console.log("in updat rows", column, row[column])
		      return {column: column, value: row[column]};
		    });
		  })
		  .enter()
		  .append('td')

    table.selectAll('tbody').selectAll('tr').selectAll("td").text(function (d) { return d.value; })

    table.selectAll('tbody').selectAll('tr').selectAll("td")
      .data(columns_new)
      .exit()
      .remove("td")

    }

    var usedaxis_list = d3.keys(data[0])

    // give select2 all the possible options
    $("#selectEvents").select2({data: Object.keys(data[0])})

    //intialialize the values with the same options (for now)
    $("#selectEvents").val(Object.keys(data[0])).trigger("change")

    // bind a callback when something is selected or unselected;
    $("#selectEvents").on("select2:select", function(e) {

        // add a new column to the parallel coordinates
        console.log('adding something', e.params.data.id);
        console.log("hideaxis_list (before)", hideaxis_list);
        usedaxis_list.push(e.params.data.id)
        hideaxis_list.splice(hideaxis_list.indexOf(e.params.data.id), 1 );
        console.log("hideaxis_list (after)", hideaxis_list);

        parcoords.hideAxis(hideaxis_list)
        .render()
        .updateAxes();

        update(usedaxis_list)
    });

        $("#selectEvents").on("select2:unselect", function(e) {

        // remove a column from the parallel coordinates
        hideaxis_list.push(e.params.data.id)
        usedaxis_list.splice(usedaxis_list.indexOf(e.params.data.id), 1 );
        console.log("removing soething", e.params.data.id);
        console.log("hideaxis_list", hideaxis_list);
        console.log("usedaxis_list", usedaxis_list);
        console.log("eee", e, e.params);
        //parcoords.hideAxis(hideaxis_list).updateAxes();
        parcoords.hideAxis(hideaxis_list)
        .render()
        .updateAxes();

         update(usedaxis_list)

    });
});


d3.json("envs_descr.json", function(data) {
    //console.log("env descr", keys(data));
    envs = data;

    function tabulate(data, columns, key) {
        var table = d3.select('#envs')
        table.append('table').append("caption").text(key).style("color", "#2c48a8")
        var thead = table.append('thead')
        var	tbody = table.append('tbody');
        console.log("col in tabular", columns)
        console.log("data in tabular", data)
        // append the header row
        thead.append('tr')
          .selectAll('th')
          .data(columns).enter()
          .append('th')
          .style("color", "#2c48a8")
            .text(function (column) { return column; })
          .style("border", "1px solid black");

        // create a row for each object in the data
        var rows = tbody.selectAll('tr')
          .data(data)
          .enter()
          .append('tr')
          .style("border", "1px solid black");

        // create a cell in each row for each column
        var cells = rows.selectAll('td')
          .data(function (row) {
            return columns.map(function (column) {
              return {column: column, value: row[column]};
            });
          })
          .enter()
          .append('td')
            .text(function (d) { return d.value; })
          .style("border", "1px solid #2c48a8")
          .style("padding", "6px");

      return table;
    }


  var softkeys = Object.keys(data);
  console.log("env descr", softkeys);
  for (k in softkeys){
  console.log("key", k, softkeys[k], data[softkeys[k]]);
    tabulate(data[softkeys[k]], ["version", "description"], softkeys[k])
    d3.select('#envs').append("BBB")
  }
});

//for barplots
// TODO:
//1. odseparowac testy dla grupy i pojedynczych elementow
//2. jak traktowac poszczegolne elementy
//3. wywalic na stale wpisane testname_eg
//4. obliczac max i dostosowywac rysowanie
//5.(?) rozne kolory dla roznych env?
//6.(?) polaczyc scatter plot z barplot
d3.csv("output_all.csv", function(data) {
        testname_eg = "regr:rel_error";

        function barplots(data, testname) {
            values_test = []
            data.forEach(function(d,i){
                if(d[testname].length > 0) {values_test.push(d[testname])}
                else {values_test.push(NaN)}
            })
            console.log("values_test", values_test)

            var bars = d3
                .select("#barplot")
                .selectAll(".barContainer")
                .data(values_test)
                .enter()
                .append("div")
                .attr("class", "barContainer");

            bars.append("div").attr("class", "barText");

            bars.append("div").attr("class", "bar").style("width", 0);

            // update text
            d3.select("#barplot").selectAll(".barText").data(data).text(function(d) {
                return d.env + ", " + d.index_name;
            });

            // update data
            d3.select("#barplot")
              .selectAll(".bar")
              .data(values_test)
              .transition()
              .duration(1000)
              .style("width", function(d) {
              // TODO should calculated max
              if (d>0) {return 100*d+"px"} else {return "1px"}
              })
              .text(function(d) {
                //TODO 100 should be probably removed
                return (100*d).toFixed(1)});


            // this is so things look nice
            //  d3.select("#barplot").selectAll(".bar").each(function(d) {
            //    if (d) {
            //      d3.select(this).style("padding-right", "5px");
            //    } else {
            //      d3.select(this).style("padding-right", "0px");
            //    }
            //  });

            // TODO: try moving to style
            document.getElementById("left").style.marginLeft = "50px";
             document.getElementById("right").style.marginLeft = "10px";
        };

        barplots(data, testname_eg);

        // select options (wasn't able to use from Anisha examples, so using similar to previous)
        var keys_all = Object.keys(data[0]);
        keys_tests = [];
        keys_all.forEach(function(d,i){if(d.startsWith("regr") || d.startsWith("stat")){keys_tests.push(d)}})
        console.log("keys_tests: ", keys_tests)


        // give select2 all the possible options
        $("#histSelect").select2({data: keys_tests})

        //initialize the value
        $("#histSelect").val(testname_eg).trigger("change")

        // changing barplot when option is changed
        $("#histSelect").on("select2:select", function(e) {
        console.log('changes in histSelect', e.params.data.id);
         barplots(data, e.params.data.id);
        })
})




//TODO
// scatter plots with axis
d3.csv("output_all.csv", function(data) {
        x_eg = "regr:rel_error";
        y_eg = "regr:abs_error";

    function axis(data, x_var, y_var) {
        var margin = { top: 30, right: 30, bottom: 30, left: 60 };
        var width = 430 - margin.left - margin.right;
        var height = 330 - margin.top - margin.bottom;



        var xValue = function(d){
            if(d[x_var].startsWith("env") || d[x_var].startsWith("vers")) {return +d[x_var].split("_")[1]}
            else if(d[x_var].length > 0) {return +d[x_var]}
            else {return null}
            }

        var yValue = function(d){
            if(d[y_var].startsWith("env") || d[y_var].startsWith("vers")) {return +d[y_var].split("_")[1]}
            if(d[y_var].length > 0) {return +d[y_var]}
            else {return null}
            }


        console.log("X MIN", d3.max(data, xValue))
        console.log("Y MIN", d3.max(data, yValue))

        var x_min = d3.min(data, xValue)
        var x_max = d3.max(data, xValue)
        var y_min = d3.min(data, yValue)
        var y_max = d3.max(data, yValue)

        var xScale = d3.scale.linear()
        .domain([x_min, 1.2*x_max])
        .range([0,width]);

        var yScale = d3.scale.linear()
        .domain([y_min, 1.1*y_max])
        .range([height,0]);

        // TODO: adding more colors
        var colorScale = d3.scaleOrdinal()
        .range(["#1ac6cf", "#e35dd4", "#66cc00", "#1a1aff", "#FF7F50", "#8B008B",
                "#00BFFF", "#FFD700", "#808080", "#008000", "#FFC0CB", "#8B4513"]);


        var chart = d3.select(".chart")
                      .attr("width",width + margin.left + margin.right+30)
                      .attr("height",height + margin.top + margin.bottom)
                      .append("g")
                      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")


        var xAxis = d3.svg.axis()
            .scale(xScale)
            .orient("bottom")
            //.ticks(1);

        var yAxis = d3.svg.axis()
            .scale(yScale)
            .orient("left")
            //.ticks(5); //doesnt work

        chart.append("g")
            .attr("transform", "translate(0," + height + ")")
            .attr("class","x axis")
            .call(xAxis)
            .append("text")
            .attr("class", "label")
            .attr("x", width)
            .attr("y", -6)
            .attr("dx", "-4.71em")


        chart.append("g")
            .attr("class","y axis")
            .call(yAxis)
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", -50)
            .attr("x", -10)
            .attr("dx", "-14.71em");


        return {
            svg: chart,
            xScale: xScale,
            yScale: yScale,
            colorScale: colorScale,
            xAxis: xAxis,
            yAxis: yAxis
          };
    };

    function scatter(ax, data, x_var, y_var){

        var xValue = function(d){
           console.log("AAA", x_var, d, d[x_var])
            if(d[x_var] == undefined){console.log("BBB", x_var, d, d[x_var])}
            else if(d[x_var].split("_").length == 2) {return +d[x_var].split("_")[1]}
            else if(d[x_var].length > 0 && isFinite(+d[x_var])) {return +d[x_var]}
            else {return null}
            }

        var yValue = function(d){
            if(d[y_var].split("_").length == 2) {return +d[y_var].split("_")[1]}
            else if(d[y_var].length > 0 && isFinite(+d[y_var])) {return +d[y_var]}
            else {return null}
            }

        var x_min = d3.min(data, xValue)
        var x_max = d3.max(data, xValue)
        var y_min = d3.min(data, yValue)
        var y_max = d3.max(data, yValue)


        // if min and max are the same is hard call Scale.domain
        if(x_min == x_max && x_min != 0.){x_min = 0.9 * x_min; x_max = 1.1 * x_max}
        else if(x_min == x_max && x_min == 0.){x_min = -0.1; x_max = 0.1}
        if(y_min == y_max && y_min != 0.){y_min = 0.9 * y_min; y_max = 1.1 * y_max}
        else if(y_min == y_max && y_min == 0.){y_min = -0.1; y_max = 0.1}


        // set domain again in case data changed bounds
        ax.xScale.domain([x_min, 1.2*x_max]);
        ax.yScale.domain([y_min, 1.1*y_max]);


        // colors
        var colorValue = function(d){return +d["env"].split("_")[1]}
        color_max = d3.max(data, colorValue)
        color_range = Array.from(Array(color_max+1).keys())
        console.log("COLOR", color_range)

        //redraw axis
        ax.svg.selectAll(".x.axis").call(ax.xAxis).selectAll(".label").text(x_var);
        ax.svg.selectAll(".y.axis").call(ax.yAxis).selectAll(".label").text(y_var);

        //add data
        ax.svg
          .selectAll(".dot")
          .data(data)
          .enter()
          .append("circle")
          .attr("class", "dot");

        //update data
        ax.svg
          .selectAll(".dot")
          .transition()
          .duration(2000)
          .attr("cx", function(d) {
            //console.log("xValue", x_var, xValue(d), ax.xScale(xValue(d)))
            return ax.xScale(xValue(d));
          })
          .attr("cy", function(d) {
            //console.log("yValue", y_var, yValue(d), ax.yScale(yValue(d)))
            return ax.yScale(yValue(d))})
          .style("fill", function(d){
          console.log("COLOR, ", colorValue(d),ax.colorScale(colorValue(d)) )
          return ax.colorScale(colorValue(d))});


        // adding legend with colors (probably should be in axis)
        var legend = ax.svg.selectAll(".legend")
                           .data(color_range)
                           .enter().append("g")
                           .attr("class", "legend")
                           .attr("transform", function(d, i) { return "translate(10," + i * 15 + ")"; });

        legend.append("circle")
              .attr("class", "dot_legend")
              .attr("x", 400)
              .attr("transform", "translate(330, 10)")
              .style("fill", function(d){return ax.colorScale(d)});

        // draw legend text
        legend.append("text")
              .attr("x", 370)
              .attr("transform", "translate(20, 0)")
              .attr("y", 9)
              .attr("dy", ".35em")
              .style("text-anchor", "end")
              .text(function(d) {return "env_"+d;})
              //.style("color", "DarkBlue") //TODO


        // try adding events here (mouseover to black)
        //TODO

        // not sure if needed at the end
        //remove dots
//        ax.svg
//          .selectAll(".dot")//
//          //.selectAll("circle")
//          .data(data)
//          .exit()
//          .remove(".dot");
//          .transition()
//          .duration(1000)
//          .style("opacity", 1e-6)
//          .attr("cy", function(d) {
//            return 0;
//          })
//          .remove(".dot");
    }

    ax = axis(data, x_eg, y_eg);
    scatter(ax, data, x_eg, y_eg);

    var x_cur = x_eg;
    var y_cur = y_eg;


    var keys_all = Object.keys(data[0]);

    // give select2 all the possible options
    $("#xSelect").select2({data: keys_all})

    //initialize the value
    $("#xSelect").val(x_eg).trigger("change")

    // changing barplot when option is changed
    $("#xSelect").on("select2:select", function(e) {
     x_cur = e.params.data.id;
     console.log('changes in xSelect', x_cur, y_cur);
     scatter(ax, data, x_cur, y_cur)
    })

    // give select2 all the possible options
    $("#ySelect").select2({data: keys_all})

    //initialize the value
    $("#ySelect").val(y_eg).trigger("change")

    // changing barplot when option is changed
    $("#ySelect").on("select2:select", function(e) {
     y_cur = e.params.data.id;
     console.log('changes in ySelect', x_cur, y_cur);
     scatter(ax, data, x_cur, y_cur)
    })

})
