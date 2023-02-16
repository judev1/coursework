function update_status(event) {

    // Create a FormData object
    var formData = new FormData();

    // Add the status and event_id to the request
    var status = $(event.target).attr("status");
    var event_id = $(event.target).parent().attr("event-id");
    var heat = $(event.target).parent().attr("heat");
    formData.append("status", status);
    formData.append("event_id", event_id);
    formData.append("heat", heat);

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/update_event_status");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status === 200) {
            // If the request was successful, update the status
            var status = JSON.parse(xhr.responseText)["status"]
            $(event.target).attr("status", status);
        } else {
            alert(xhr.responseText)
        }
    }

    // Send the request
    xhr.send(formData);
}