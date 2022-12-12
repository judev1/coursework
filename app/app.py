# Imports the Flask object within the flask module
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

# Initiates the Flask object and sets the 'static' folder as the template folder
app = Flask(__name__, template_folder='static')


# Imports the Database object from the database module
from database import Database

# Initialises the Database object
db = Database('app/database.db')


class FakeUser:
	is_admin = False

class FakeAdmin:
	is_admin = True


# The route for the main page
@app.route('/', methods=['GET'])
def main():
    return render_template(
        'template.html',
        main=True,
        user=None,
        active_gala=False,
        live_gala=False
    )

# The route for the login page
@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

# The route for the login method
@app.route('/login', methods=['POST'])
def login_method():

    # Checks if the email has been provided
    if 'email' in request.form:

        # Gets the email from the form
        email = request.form['email']

        # Checks if the email is in the database
        if not db.check_email(email):
            return 'Email is not associated with an account'

        # Checks if the password has been provided
        if 'password' in request.form:

            # Gets the password from the form
            password = request.form['password']
            print(password)

            # Checks if the password is correct
            if not db.check_password(email, password):
                return 'Password is incorrect'

            # If the email and password pass all the checks
            expiry = 59*60*24*7
            token = db.generate_token(email, expiry)

            response = redirect('/')
            response.set_cookie('token', token, max_age=expiry)
            return response

        return 'Password was not provided'

    return 'Email was not provided'


# Checks to see if the current file is the one being run (ie if another file
# called it then the app should have been run already, this file should on be run
# by itself for debugging)
if __name__ == '__main__':

	# Runs the app with debugging
	app.run(debug=True, use_reloader=False)