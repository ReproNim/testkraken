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
            data.forEach(function(d,i){values_test.push(d[testname])})
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
              if (d>0) {return 50000*d+"px"} else {return "1px"}
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
        };

        barplots(data, testname_eg);

        // select options (wasn't able to use from Anisha examples, so using similar to previous)
        var keys_all = Object.keys(data[0]);
        keys_tests = [];
        keys_all.forEach(function(d,i){if(d.startsWith("regr")){keys_tests.push(d)}})
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
//for barplots with axis
d3.csv("output_all.csv", function(data) {
        testname_eg = "regr:rel_error";

        function axis(data, testname) {

        var margin = 30;
        var width = 800;
        var height = 300;

        var xScale = d3.scale.ordinal()
        .domain([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27])
        .rangeBands([0,width]);

        var yScale = d3.scale.linear()
        .domain([0,0.1])
        .range([height,0]);

        var chart = d3.select(".chart")
        chart.attr("width",width + 2*margin)
            .attr("height",height + 2*margin)
            .append("g")
                .attr("transform","translate(" + margin + "," + margin + ")")
//            .selectAll("rect")
//            .data(data)
//            .enter().append("rect")
//            .attr("width", 30)
//            .attr("height",function(d) { return height - yScale(d); })
//            .attr("x",function(d,i) { return xScale(i); })
//            .attr("y",function(d) { return yScale(d); });


        var xAxis = d3.svg.axis()
            .scale(xScale)
            .orient("bottom")
            //.ticks(1);

        //cos jest zle ze scale y albo left orient
        var yAxis = d3.svg.axis()
            .scale(yScale)
            .orient("left")
            //.ticks(5); //doesnt work

        chart.append("g")
            .attr("transform", "translate(" + margin + "," + (height+margin) + ")")
            .attr("class","x axis")
            .call(xAxis);

        chart.append("g")
            .attr("transform", "translate(" + margin + "," + margin + ")")
            .attr("class","y axis")
            .call(yAxis);

        return {
            svg: chart,
            xScale: xScale,
            yScale: yScale,
//            xValue: xValue,
//            yValue: yValue,
            xAxis: xAxis,
            yAxis: yAxis
          };
    };

    function barplots(ax, data, testname) {
          // set domain again in case data changed bounds
//          xScale.domain([d3.min(data, ax.xValue), d3.max(data, ax.xValue)]);
          ax.yScale.domain([0.,1]);

        //redraw axis
        ax.svg.selectAll(".x.axis").call(ax.xAxis);
        ax.svg.selectAll(".y.axis").call(ax.yAxis);


        values_test = []
        data.forEach(function(d,i){values_test.push(d[testname])})
        values_bar_test = []
        values_test.forEach(function(d){values_bar_test.push(10000*d)})
        console.log("values_test", values_test)

        //add data
        ax.svg
            .selectAll(".bar")
            .data(values_test)
            .enter()
            .append("div")
            .attr("class", "bar")
            .text(function(d){return (100*d).toFixed(1)});

        ax.svg.selectAll(".bar").data(values_bar_test)
            .style("height", function(d){return d + "px";})
            .style("margin-top", function(d){return (100-d) + "px";})


//        values_test = []
//        data.forEach(function(d,i){values_test.push(d[testname])})
//        values_bar_test = []
//        values_test.forEach(function(d){values_bar_test.push(10000*d)})
//        console.log("values_test", values_test)
//
//        //var mybar = d3.select("#barplot").selectAll(".bar")
//        d3.select("#barplot").selectAll(".bar")
//        .data(values_test)
//        .enter().append("div")
//        .attr("class", "bar")
//        //.text(function(d){return (100*d).toFixed(1)});
//
//        d3.select("#barplot").selectAll(".bar").data(values_bar_test)
//        .style("height", function(d){return d + "px";})
//        .style("margin-top", function(d){return (100-d) + "px";})
    };



    ax = axis(data, testname_eg);
    barplots(ax, data, testname_eg);

})
