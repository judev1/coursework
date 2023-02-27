function get_live_race() {

    // Create a FormData object
    var formData = new FormData();
    var lane_id = $("#lane").attr("lane-id")
    formData.append("lane_id", lane_id);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/get_live_race", false);

    // Send the data to the server
    xhr.send(formData);

    // Check the status of the response
    if (xhr.status == 200) {
        // If the response is OK update the page
        var data = JSON.parse(xhr.responseText);
        var event = data["event"];
        var swimmers = data["swimmers"];
        $("#event").text(event);
        $("#swimmers").text(swimmers);

        // Remove the reload onclick event from the stopwatch tag
        $("#stopwatch").removeAttr("onclick");
        $("#stopwatch").attr("status", "ready");
    }
}

$(document).ready(function() {
    get_live_race();
});