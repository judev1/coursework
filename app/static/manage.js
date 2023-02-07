function update_gala(event) {

    // Get the user id from the meta tag
    var user_id = $("meta[name='user_id']").attr("content");

    // Get the fields from the form
    var schools = $("#schools").val();
    var host = $("#host").val();
    var date = $("#date").val();

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