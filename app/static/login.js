// Regex for email validation
const email_re = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;

// Checks the fields and returns true if they are valid
const validatefields = function() {

	// Checks if either the email is invalid or the password is empty
	if (!email_re.test($("#email").val()) || $("#password").val() == "") {

		// Checks if the email is invalid
		if (!email_re.test($("#email").val())) {
			// Shows the error message if the email is invalid
			$("#invalid-email").show();
		};

		// Checks if the password is empty
		if ($("#password").val() == "") {
			// Shows the error message if the password is empty
			$("#empty-password").show();
		};

		// Tells the form not to submit
		return false;
	};

	// Otherwise allows the form to submit
	return true;
};


// Function called once the entire document has been rendered
$(document).ready(function() {

	// Hides the error messages
	$("#invalid-email").hide()
	$("#empty-password").hide()

	// When the user clicks out of the email field
	$("#email").change(function() {
		// Checks if the email is invalid
		if (!email_re.test($(this).val())) {
			// Shows the error message if the email is invalid
			$("#invalid-email").show();
		};
	});

	// When the user types in the email field
	$("#email").bind("input propertychange", function() {
		// Checks if the email is valid
		if (email_re.test($(this).val())) {
			// Hides the error message if the email is now valid
			$("#invalid-email").hide();
		};
	});

	// When the user types in the password field
	$("#password").bind("input propertychange", function() {
		// Checks if the password is empty
		if ($(this).val() != "") {
			// Hides the error message if the password is empty
			$("#empty-password").hide();
		};
	});
});
