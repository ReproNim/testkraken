var parcoords;
var dataset;
var dataView;


d3.csv("results.csv", function(data) {

    "use strict";

    data.forEach(function (d, i) {
        d.id = d.id || i;
    });

    dataset = data;

    var colors = {
      "pass": "green",
      "fail": "red",
      "error": "gray"
    };

    function colorByResult(result) {
        return colors[result.toLowerCase()];
    }

    parcoords = d3.parcoords()("#parcoord-plot")
    .data(data)
    .alpha(0.5)
    .mode("queue")
    .rate(30)
    .margin({ top: 30, left: 0, bottom: 20, right: 0 })
    .hideAxis(["id"])
    .color(function(d) {return colorByResult(d.result);})
    .render()
    .reorderable()
    .brushMode("1D-axes")
    .autoscale();

    // slickgrid
    var column_keys = d3.keys(data[0]);
    console.log(column_keys);

    var options = {
        enableCellNavigation: true,
        enableColumnReorder: false,
        multiColumnSort: false,
        forceFitColumns: true
    };

    var columns = column_keys.map(function (key, i) {
        return {
            id: key,
            name: key,
            field: key,
            sortable: false
        };
    });

    dataView = new Slick.Data.DataView();
    var grid = new Slick.Grid("#grid", dataView, columns, options);
    var pager = new Slick.Controls.Pager(dataView, grid, $("#pager"));

    function gridUpdate(data) {
        dataView.beginUpdate();
        dataView.setItems(data);
        dataView.endUpdate();
    }

    // fill grid with data
    gridUpdate(data);


    // TODO(kaczmarj): change colors based on column clicked. Do something
    // similar to MetaSearch: use discrete colors for discrete classes and
    // continuous color pallete for continuous variables.
    //
    // parcoords.svg
    // .selectAll(".dimension")
    // .on("click", changeColor);

    // Add useful charts for results. Here we plot brain volume.
    // TODO+QUESTION(kaczmarj): what should plots look like? Should they
    // be comparisons to the reference data?
    var chart = c3.generate({
        bindto: "#chart-bar-brainvolume",
        data: {
            json: data,
            type: "bar",
            keys: {
                value: ["brainvolume"]
            }
        }
    });

});
