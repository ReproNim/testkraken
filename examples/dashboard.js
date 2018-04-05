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
    // var pager = new Slick.Controls.Pager(dataView, grid, $("#pager"));

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


    // Add plot of data[column] to HTML, and render.
    // column is a string of a column name in data.
    function createPlot(column) {
        // create new div in the html page.
        var this_div = document.createElement('div');
        // assign this div some unique id. the plot requires this id.
        this_div.id = column.replace(/:/g, "-");
        // get the div container plot.
        var plots_container_div = document.getElementById("plots");
        // append the new div into this container div.
        plots_container_div.appendChild(this_div);

        // create plot.
        var chart = c3.generate({
            bindto: "#" + this_div.id,
            data: {
                json: data,
                type: "bar",
                keys: {
                    value: [column]
                }
            }
        });
    }


    // Create new array of keys from which we will plot.
    // Exclude these keys as an example.
    var exclude_keys = ["id", "base", "ants", "freesurfer", "mindboggle"];
    var plot_keys = column_keys.filter(column_keys => !exclude_keys.includes(column_keys));

    // create one plot for each column.
    plot_keys.map(createPlot)

    // create one plot for one column.
    // createPlot('brainvolume')

});
