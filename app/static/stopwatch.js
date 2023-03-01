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
        $("#stopwatch").attr("onclick", "toggle_stopwatch()");
        $("#stopwatch").attr("status", "ready");
    }
}

function start_stopwatch(display) {
    var start = new Date().getTime();
    var timer = setInterval(function() {
        var time = Math.floor((new Date().getTime() - start));
        var minutes = Math.floor(time / 60000);
        var seconds = Math.floor((time % 60000) / 1000);
        var milliseconds = Math.floor((time % 1000) / 10);
        // Add leading zeros to seconds and milliseconds
        minutes = (minutes < 10) ? "0" + minutes : minutes;
        seconds = (seconds < 10) ? "0" + seconds : seconds;
        milliseconds = (milliseconds < 10) ? "0" + milliseconds : milliseconds;
        display.text(text = minutes + ":" + seconds + ":" + milliseconds);
    }, 50);

    display.data("timer", timer);
}

function record_time() {

    // Get the volunteer id and code from the URL
    var url = new URL(window.location.href);
    var path = url.pathname.split("/");
    var volunteer_id = path[2];
    var volunteer_code = path[3];

    // Get the time from the stopwatch display
    var time = $("#stopwatch").find(".display").text();

    // Create a FormData object
    var formData = new FormData();
    formData.append("volunteer_id", volunteer_id);
    formData.append("volunteer_code", volunteer_code);
    formData.append("time", time);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/record_time", false);

    // Send the data to the server
    xhr.send(formData);
}

function toggle_stopwatch() {
    var stopwatch = $("#stopwatch");
    var display = stopwatch.find(".display");
    if (stopwatch.attr("status") == "running") {
        // Stop the timer
        clearInterval(display.data("timer"));
        // Send the time to the server
        record_time();
        // Clear the display and set the status to inactive
        display.text("");
        $(".volunteer-text #swimmers").text("");
        $(".volunteer-text #event").text("");
        stopwatch.attr("status", "inactive");
        // Add back the onclick event
        stopwatch.attr("onclick", "get_live_race()");
    } else if (stopwatch.attr("status") == "ready") {
        stopwatch.attr("status", "running")
        start_stopwatch(display);
    }
}

$(document).ready(function() {
    get_live_race();
});