// Checks if the character is a number
function isNum(char) {
    return !isNaN(char);
}

// Checks if the character is a letter
function isAlpha(char) {
    return isNaN(char) && char.toLowerCase() !== char.toUpperCase();
}

// Checks if the character is a lowercase letter
function isLower(char) {
    return isAlpha(char) && char === char.toLowerCase();
}

// Checks if the character is an uppercase letter
function isUpper(char) {
    return isAlpha(char) && char === char.toUpperCase();
}

// Checks if the character is a special character
function isAlphaNum(char) {
    return isNum(char) || isAlpha(char);
}


// Checks if the password is valid
function checkPassword(password) {
    // Check if password is at least 8 characters long
    if (password.length < 8) {
        message = "password must be at least 8 characters long";
        return false;
    }
    // Check if password contains at least one digit
    if (!password.split('').some(char => isNum(char))) {
        message = "password must contain at least one digit";
        return false;
    }
    // Check if password contains at least one uppercase letter
    if (!password.split('').some(char => isUpper(char))) {
        message = "password must contain at least one uppercase letter";
        return false;
    }
    // Check if password contains at least one lowercase letter
    if (!password.split('').some(char => isLower(char))) {
        message = "password must contain at least one lowercase letter";
        return false;
    }
    // Check if password contains at least one special character
    if (password.split('').every(char => isAlphaNum(char))) {
        message = "password must contain at least one special character";
        return false;
    }
    return true;
}

var message = "";


// Function called once the entire document has been rendered
$(document).ready(function() {

	// Hides the error messages
	$("#invalid-password").hide()

	// When the user clicks out of the password field
	$("#password").change(function() {
		// Checks if the password is invalid
		if (!checkPassword($(this).val())) {
			// Shows the error message if the password is invalid
			$("#invalid-password").show();
            $("#invalid-password").text(message);
		};
	});

	// When the user types in the password field
	$("#password").bind("input propertychange", function() {
		// Checks if the password is valid
		if (checkPassword($(this).val())) {
			// Hides the error message if the password is now valid
			$("#invalid-password").hide();
		};
	});
});
