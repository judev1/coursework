function updatehosts() {

    // Gets the values and names of the selected schools
    var values = $(".selectpicker[name=schools]").val();
    var names = $(".selectpicker[name=schools]").find("option:selected").map(
        function() { return this.text; }
    ).get();

    // Removes all schools except the first one
    $(".selectpicker[name=host] option").slice(1).each(function() {
        $(this).remove();
    })

    // If no schools are selected, refresh the selectpicker and return
    if (values == null) {
        $(".selectpicker[name=host]").selectpicker("refresh");
        return;
    }

    // Adds all schools
    for (var i = 0; i < values.length; i++) {
        var option = $("<option>").attr("value", values[i]).text(names[i]);
        $(".selectpicker[name=host]").append(option);
    }

    // Refresh the selectpicker
    $(".selectpicker[name=host]").selectpicker("refresh");
}