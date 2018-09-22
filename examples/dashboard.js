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
		      console.log("in updat rows", column, row[column])
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