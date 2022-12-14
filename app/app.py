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


class User:

    def __init__(self, details):

        self.user_id = details[0]
        self.school_id = details[1]
        self.email = details[2]

        self.name = details[4]
        self.surname = details[5]
        self.gender = details[6]
        self.has_picture = details[7]
        self.coach = details[8]
        print(details)

        if not self.coach:

            details = db.get_student(self.user_id)
            print(details)
            self.graduation_year = details[1]
            self.fav_stroke = details[2]
            self.captain = details[3]
            self.is_swimming = details[4]

    def is_admin(self):
        return self.coach or self.captain

# Checks a user's token
def check_token():

    # Checks if the user has a token
    if 'token' in request.cookies:
        token = request.cookies['token']

        # Checks if the token is valid
        if db.check_token(token):
            return True

        # If the token is invalid, delete it
        redirect("/").delete_cookie('token')

    return False

# Gets a user with a token
def get_user():
    if check_token():
        token = request.cookies['token']
        user_id = db.get_user_id(token)
        details = db.get_user(user_id)
        return User(details)


# The route for the main page
@app.route('/', methods=['GET'])
def main():
    return render_template(
        'template.html',
        main=True,
        user=get_user(),
        active_gala=False,
        live_gala=False
    )

# The route for the login page
@app.route('/login', methods=['GET'])
def login():
    # Checks if the user is already logged in
    if check_token():
        return redirect('/')
    return render_template('login.html')

# The route for the login method
@app.route('/login', methods=['POST'])
def login_method():

    # Checks if the user is already logged in
    if check_token():
        return redirect('/')

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