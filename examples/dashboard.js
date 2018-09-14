var parcoords;
var dataset;
var dataView;


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
        .render()
        .reorderable()
        //.brushMode("1D-axes")
        .autoscale();



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
		    .style('background-color', 'black')
		    .style('color', 'white')
		    .style("border", "2px solid green")
		    .style("padding", "6px");

		// create a row for each object in the data
		var rows = tbody.selectAll('tr')
		  .data(data)
		  .enter()
		  .append('tr')
		  .style("background-color", function(d, i){
		    if ( i % 2) {
		        return 'pink';
		    } else {
		        return 'blue';
		    }
		  })
		  .style("border", "1px solid green")
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
		    .style("border", "2px solid green")
		    .style("padding", "6px")
		    ;

	//  return table;
	//}

	// render the table(s)
	//tabulate(data, d3.keys(data[0]))
    //grid.append(tabulate(grid, data, d3.keys(data[0])));

    function update(columns_new){
    table.selectAll("th")
          .data(columns_new)
      .enter()
      .append("th")

    table.selectAll("th")
        .text(function(d, i){
          return d
        })

    table.selectAll("th")
        .data(columns_new)
        .exit()
        .remove("th")


	tbody.selectAll('tr')
		  .data(data)
		  .enter()
		  .append('tr')
		  .style("background-color", function(d, i){
		    if ( i % 2) {
		        return 'pink';
		    } else {
		        return 'blue';
		    }
		  })
		  .style("border", "1px solid green")
		  .style("padding", "6px")
		  ;
    console.log("data(columns_new)", data);

    tbody.selectAll("tr")
      .data(data)
      .exit()
      .remove("tr")


    rows.selectAll("td")
      .data(columns_new)
      .enter()
      .append("td")


    rows.selectAll("td")
		  .data(function (row) {
		    return columns_new.map(function (column) {
		      return {column: column, value: row[column]};
		    });
		  })
		  .enter()
		  .append('td')

    rows.selectAll("td")
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

        update(["base"])


    });

        $("#selectEvents").on("select2:unselect", function(e) {

        // remove a column from the parallel coordinates
        hideaxis_list.push(e.params.data.id)
        usedaxis_list.splice(usedaxis_list.indexOf(e.params.data.id), 1 );
        console.log("removing soething", e.params.data.id);
        console.log("hideaxis_list", hideaxis_list);
        //parcoords.hideAxis(hideaxis_list).updateAxes();
        parcoords.hideAxis(hideaxis_list)
        .render()
        .updateAxes();

         update(["ants"])

    });




});
