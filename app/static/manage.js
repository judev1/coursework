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

function get_swimmers(event_id) {

    // Create a FormData object
    var formData = new FormData();
    formData.append("event_id", event_id);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/get_swimmers", false);

    // Send the data to the server
    xhr.send(formData);

    return JSON.parse(xhr.responseText);
}

function add_lane_to_table(lane_id) {

    // Add a new lane column to the gala table head
    var row = $(".gala").find("thead").find("tr");
    var lane = row.find("th:not(.blank)").length + 1;
    row.append("<th>Lane " + lane + "</th>");

    // Add the lane id to the cell
    row.find("th").last().attr("lane-id", lane_id);

    // Add a remove lane buttons to the gala table body
    var remove_row = $(".gala").find("tbody").find("tr")[0];
    $(remove_row).append("<td class='remove-lane' onclick='remove_lane(event)'>remove</td>");

    // Add a new lane column to the gala table body
    $(".gala").find("tbody").find("tr").slice(1).each(function() {
        var html = `<td><select class='selectpicker' onchange='update_race(event)' required>
            <option selected value>--</option>`

        var event_id = $(this).attr("event-id");
        var swimmers = get_swimmers(event_id);
        swimmers.forEach(function(swimmer) {
            var important = swimmer[2] ? "important" : "";
            html += `
                <option value=${swimmer[0]} class=${important}>
                    ${swimmer[1]}
                </option>
            `;
        });
        $(this).children().eq(-2).after(html + "</select></td>");
        $(this).children().eq(-2).find("select").selectpicker();
    });
}

function add_lane(event) {

    // Create a FormData object
    var formData = new FormData();

    // Add the lane number to the request
    var row = $(".gala").find("thead").find("tr");
    var lane =  row.find("th:not(.blank)").length + 1;
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

    // Update the lane numbers in the gala table head except the blank columns
    var row = $(".gala").find("thead").find("tr");
    row.find("th:not(.blank)").each(function(index) {
        $(this).text("Lane " + (index + 1));
    });

    // Create a FormData object
    var formData = new FormData();

    // Create an dictionary of lane ids and lane numbers
    var lanes = [];
    row.find("th:not(.blank)").each(function(index) {
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

    // Remove the lane from the gala table head
    var row = $(".gala").find("thead").find("tr");
    var index = $(event.target).parent().find("td:not(.blank)").index($(event.target));
    row.find("th:not(.blank)").eq(index).remove();

    // Remove the lane from the gala table body
    index += row.find("th.blank").length;
    $(".gala").find("tbody").find("tr").each(function() {
        $(this).find("td").eq(index).remove();
    });

    // Update the lane numbers in the gala table head
    update_lane_numbers();
}

function add_event(form, response) {

    // Add a new event row to the gala table body
    $(".gala").find("tbody").append("<tr></tr>")
    var row = $(".gala").find("tbody").find("tr").last();

    // Add the event id to the row
    row.attr("event-id", response["event_id"]);

    // Include the event information in the cell
    var age_group = form.get("age_group") + " ";
    if (age_group == "all ") { age_group = ""; }
    var group = form.get("group").slice(0, 1).toUpperCase() + form.get("group").slice(1) + " ";
    var parts = form.get("parts") + "x";
    if (parts == "1x") { parts = ""; }
    var length = form.get("length") + "m ";
    var stroke = form.get("stroke").slice(0, 1).toUpperCase() + form.get("stroke").slice(1);
    var contents = age_group + group + parts + length + stroke;
    $(row).append("<td>" + contents + "</td>");

    $(row).append("<td>Heat 1</td>");

    var swimmers = get_swimmers(response["event_id"]);
    var html = `<td><select class='selectpicker' onchange='update_race(event)' required>
        <option selected value>--</option>`
        swimmers.forEach(function(swimmer) {
            var important = swimmer[2] ? "important" : "";
            html += `
                <option value=${swimmer[0]} class=${important}>
                    ${swimmer[1]}
                </option>
            `;
        });
    html += "</select></td>";

    // Fill the event row empty cells
    var lanes = $(".gala").find("thead").find("th:not(.blank)").length;
    for (var i = 0; i < lanes; i++) {
        // $(row).append("<td></td>");
        $(row).append(html).find("select").selectpicker();
    }

    // Add a remove event button at the end
    $(row).append("<td class='remove-event'><img src='static/images/cross.png' onclick='remove_event(event)'></td>");
}

function remove_event(event) {

        // Remove the event from the gala table body
        var row = $(event.target).parent().parent();
        row.remove();

        // Update the events in the database
        update_events();
}

function update_events(event) {

    // Create a FormData object
    var formData = new FormData();

    // Add the event ids to the request
    var events = [];
    $(".gala").find("tbody").find("tr").slice(1).each(function() {
        events.push(Number($(this).attr("event-id")));
    });
    formData.append("events", JSON.stringify(events));

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/update_events");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status != 200) {
            alert(xhr.responseText)
        }
    }

    // Send the data to the server
    xhr.send(formData);
}

function update_race(event) {

    // Get the lane and event id
    var cell = $(event.target).parent().parent();
    var event_id = cell.parent().attr("event-id");
    var index = cell.parent().children().index(cell)
    var lane_id = $(".gala th").eq(index).attr("lane-id");

    // Get the swimmers id
    var swimmer_ids = $(event.target).val();

    // Create a FormData object
    var formData = new FormData();
    formData.append("event_id", event_id);
    formData.append("lane_id", lane_id);
    formData.append("swimmer_ids", swimmer_ids);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/update_race");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status != 200) {
            alert(xhr.responseText)
        }
    }

    // Send the data to the server
    xhr.send(formData);
}

$(document).ready(function(){
    $(".gala").dragtable({
        // Prevents the blank (first) column from being dragged
        items: "thead th:not( .blank )",
        start: function(e, column_rows) {
            var rows = column_rows.column
            var drag_rows = column_rows.dragDisplay.find("tr");
            drag_rows.each(function(index) {
                if (index == 1) {
                    $(this).find("td").height($(rows).eq(index).height());
                } else {
                    $(this).height($(rows).eq(index).height());
                }
            });
        },
        stop: update_lane_numbers
    });

    $(".gala").sortable({
        // Prevents the head and remove row from being moved
        items: "tbody tr:not( tr:first )",
        // Only allows the name and heat columns to be dragged
        handle: "td:first, td:nth-child(2)",
        axis: "y",
        distance: 0,
        cursor: "move",
        tolerance: "intersect",
        start: function(e, ui) {
            var item = ui.item.clone();
            item.addClass("cloned");
            item.insertAfter(ui.item);
            item.css("cursor", "move")
            ui.placeholder.css("cursor", "move")

            ui.placeholder.addClass("selected placeholder")
            ui.placeholder.children().each(function(index) {
                var item = ui.item.eq(index);
                var placeholder = ui.placeholder.eq(index);
                placeholder.html(item.html());
                placeholder.css("visibility", "visible");
                // this_is_not_a_function();
            });
        },
        helper: function(e, tr) {
            var $originals = tr.children();
            var $helper = tr.clone();
            $helper.children().each(function(index) {
                var width = $originals.eq(index).width();
                var padding = $originals.eq(index).css("padding");
                $(this).css("width", "calc(" + width + "px + " + padding + "*2)");
                $(this).css("padding", padding);
            });
            $helper.css("opacity", "0.7")

            return $helper;
        },
        stop: function(e, ui) {
            $(".cloned").remove();
            update_events()
        }
    }).disableSelection()

    $("#add-event .popup form").bind('submit', function (event) {

        // Prevent the form from being submitted
        event.preventDefault();

        // Get the form data
        var form = new FormData(event.target);

        // Send the data to the server
        fetch(event.target.action, {
            method: "POST",
            body: new URLSearchParams(form)
        }).then(function (response) {
            // Check the response status
            if (response.status == 200) {
                // Add the event to the table and hide the popup
                response.json().then(function(data) {
                    add_event(form, data);
                    $('#add-event').hide();
                });
            } else {
                alert(response.text())
            }
        });
    });
});