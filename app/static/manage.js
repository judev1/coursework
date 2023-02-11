function update_gala(event) {

    // Get the fields from the form
    var schools = $(".selectpicker[name=schools]").val();
    var host = $(".selectpicker[name=host]").val();
    var date = $("input[name=date]").val();

    // Create a FormData object
    var formData = new FormData();
    formData.append("schools", schools);
    formData.append("host", host);
    formData.append("date", date);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/update_gala");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status != 200) {
            alert(xhr.responseText)
        }
    }

    // Send the data to the server
    xhr.send(formData);
}

function add_lane_to_table(lane_id) {

    // Add a new lane column to the gala table head
    var row = $(".gala").find("thead").find("tr");
    var lane = row.find("th").length;
    row.append("<th>Lane " + lane + "</th>");

    // Add the lane id to the cell
    row.find("th").last().attr("lane-id", lane_id);

    // Add a remove lane buttons to the gala table body
    var remove_row = $(".gala").find("tbody").find("tr")[0];
    $(remove_row).append("<td class='remove-lane' onclick='remove_lane(event)'>remove</td>");

    // Add a new lane column to the gala table body
    $(".gala").find("tbody").find("tr").slice(1).each(function() {
        $(this).append("<td>" + lane + "</td>");
        // Add the lane id to the cell
    });
}

function add_lane(event) {

    // Create a FormData object
    var formData = new FormData();

    // Add the lane number to the request
    var row = $(".gala").find("thead").find("tr");
    var lane =  row.find("th").length;
    formData.append("lane", lane);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/add_lane");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status == 200) {
            // Get the lane id from the json response
            var lane_id = JSON.parse(xhr.responseText).lane_id;
            // Add the lane to the table
            add_lane_to_table(lane_id);
        } else {
            alert(xhr.responseText)
        }
    }

    // Send the data to the server
    xhr.send(formData);
}

function update_lane_numbers(event) {

    // Update the lane numbers in the gala table head except the first column
    var row = $(".gala").find("thead").find("tr");
    row.find("th").slice(1).each(function(index) {
        $(this).text("Lane " + (index + 1));
    });

    // Create a FormData object
    var formData = new FormData();

    // Create an dictionary of lane ids and lane numbers
    var lanes = [];
    row.find("th").slice(1).each(function(index) {
        var lane_id = $(this).attr("lane-id");
        lanes.push([Number(lane_id), index + 1]);
    });

    // Add the lanes to the request
    formData.append("lanes", JSON.stringify(lanes));

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/update_lanes");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status != 200) {
            alert(xhr.responseText)
        }
    }

    // Send the data to the server
    xhr.send(formData);
}

function remove_lane(event) {

    // Remove the lane in which the remove button was clicked

    // Get the index of the column to be removed
    var index = $(event.target).index();
    console.log(index)

    // Remove the lane from the gala table head
    var row = $(".gala").find("thead").find("tr");
    row.find("th").eq(index).remove();

    // Remove the lane from the gala table body
    $(".gala").find("tbody").find("tr").each(function() {
        $(this).find("td").eq(index).remove();
    });

    // Update the lane numbers in the gala table head
    update_lane_numbers();
}

$(document).ready(function(){
    $(".gala").dragtable({
        // Prevents the blank (first) column from being dragged
        items: 'thead th:not( .blank )',
        stop: update_lane_numbers
    });
});