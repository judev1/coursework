function upload(event){

    // Get the file from the input
    var files = event.target.files;
    var file = files[0];

    // Create a formdata object to send the file
    var formData = new FormData();
    formData.append("file", file);

    // Get the user id from the meta tag
    var user_id = $("meta[name='user_id']").attr("content");

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/profile/" + user_id + "/upload_picture");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status == 200) {
            d = new Date();
            // The date is added to force the browser to reload the image
            // The response text is the link to the user's profile picture
            var filename = xhr.responseText + "?" + d.getTime();
            $("#profile_picture").attr("src", filename);

            // Delete all the children of the div
            $("#edit").empty();

            // Add new children to the div
            $("#edit").append("<input type='file' id='file' onchange='upload(event)'>");
            $("#edit").append("<label class='top' for='file'>change</label>");
            $("#edit").append("<img src='/static/images/edit.png'>");
            $("#edit").append("<label class='bottom' onclick='remove()'>remove</label>");

        } else {
            alert(xhr.responseText)
        }
    };

    // Send the data to the server
    xhr.send(formData);
}

function remove(event){

    // Get the user id from the meta tag
    var user_id = $("meta[name='user_id']").attr("content");

    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/profile/" + user_id + "/remove_picture");

    // Set up a handler for when the request finishes
    xhr.onload = function () {
        if (xhr.status == 200) {
            d = new Date();
            // The date is added to force the browser to reload the image
            // The response text is the link to the user's profile picture
            var filename = xhr.responseText + "?" + d.getTime();
            $("#profile_picture").attr("src", filename);

            // Delete all the children of the div
            $("#edit").empty();

            // Add new children to the div
            $("#edit").append("<input type='file' id='file' onchange='upload(event)'>");
            $("#edit").append("<img src='/static/images/edit.png'>");
            $("#edit").append("<label class='bottom' for='file'>add</label>");

        } else {
            alert(xhr.responseText)
        }
    };

    // Send the data to the server
    xhr.send();
}