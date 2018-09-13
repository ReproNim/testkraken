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

    // give select2 all the possible options
    $("#selectEvents").select2({data: Object.keys(data[0])})

    //intialialize the values with the same options (for now)
    $("#selectEvents").val(Object.keys(data[0])).trigger("change")

    // bind a callback when something is selected or unselected;
    $("#selectEvents").on("select2:select", function(e) {

        // add a new column to the parallel coordinates
        console.log('adding something', e.params.data.id);
        console.log("hideaxis_list (before)", hideaxis_list);
        hideaxis_list.splice(hideaxis_list.indexOf(e.params.data.id), 1 );
        console.log("hideaxis_list (after)", hideaxis_list);

        parcoords.hideAxis(hideaxis_list)
        .render()
        .updateAxes();

    });

    $("#selectEvents").on("select2:unselect", function(e) {

        // remove a column from the parallel coordinates
        hideaxis_list.push(e.params.data.id)
        console.log("removing soething", e.params.data.id);
        console.log("hideaxis_list", hideaxis_list);
        //parcoords.hideAxis(hideaxis_list).updateAxes();
        parcoords.hideAxis(hideaxis_list)
        .render()
        .updateAxes();
    });




    // slickgrid
//    var column_keys = d3.keys(data[0]);

//    var options = {
//        enableCellNavigation: true,
//        enableColumnReorder: false,
//        multiColumnSort: false,
//        forceFitColumns: true
//    };

//    var columns = column_keys.map(function (key) {
//        return {
//            id: key,
//            name: key,
//            field: key,
//            sortable: false
//        };
//    });

//    dataView = new Slick.Data.DataView();
//    var grid = new Slick.Grid("#grid", dataView, columns, options);
    // var pager = new Slick.Controls.Pager(dataView, grid, $("#pager"));

//    function gridUpdate(data) {
//        dataView.beginUpdate();
//        dataView.setItems(data);
//        dataView.endUpdate();
//    }

    // fill grid with data
//    gridUpdate(data);


});
