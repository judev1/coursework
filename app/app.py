# Imports the Flask object within the flask module
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import send_file

import magic
import os
import datetime

# Initiates the Flask object and sets the 'static' folder as the template folder
app = Flask(__name__, template_folder='static')

# Creates a new Magic object for getting the file type
mime = magic.Magic(mime=True)


# Imports the Database object from the database module
from database import Database

# Initialises the Database object
db = Database('app/database.db')


STROKES = [
    'frontcrawl',
    'backcrawl',
    'breaststroke',
    'butterfly',
    'medley'
]


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

        if not self.coach:

            details = db.get_student(self.user_id)
            self.graduation_year = details[1]
            self.fav_stroke = details[2]
            self.captain = details[3]
            self.is_swimming = details[4]

    @property
    def year(self):
        years = {
            13: 'XX',
            12: 'LXX',
            11: 'D Block',
            10: 'E Block',
            9: 'F Block',
        }
        diff = datetime.datetime.now().year
        year = 13 - (self.graduation_year - diff)
        if year in years:
            return years[year]
        return f"{self.graduation_year} Leaver"

    def is_admin(self):
        return self.coach or self.captain

    def is_owner(self, user):
        coach = self.coach and self.school_id == user.school_id
        owner = self.user_id == user.user_id
        return coach or owner

# Checks a user's token
def check_token():

    # Checks if the user has a token
    if 'token' in request.cookies:
        token = request.cookies['token']

        # Checks if the token is valid
        if db.check_token(token):
            return True

        # If the token is invalid, delete it
        redirect('/').delete_cookie('token')

    return False

# Gets a user from an id
def get_user(user_id):
    details = db.get_user(user_id)

    # Returns a User object if the user_id was valid
    if details:
        return User(details)

# Gets the logged in user
def get_logged_in_user():
    if check_token():
        token = request.cookies['token']
        user_id = db.get_user_id(token)
        return get_user(user_id)


# The route for the main page
@app.route('/', methods=['GET'])
def main():
    return render_template(
        'template.html',
        main=True,
        user=get_logged_in_user(),
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

# The route for the profile page
@app.route('/profile', methods=['GET'])
def profile():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user_id = db.get_user_id(token)
    user = get_user(user_id)

    if user.coach:

        school_id = user.school_id
        swimmers = map(User, db.get_students(school_id))

        return render_template(
            'coachprofile.html',
            main=False,
            user=user,
            user_page=user,
            swimmers=swimmers,
            active_gala=False,
            live_gala=False
        )

    return render_template(
        'profile.html',
        main=False,
        user=user,
        user_page=user,
        active_gala=False,
        live_gala=False
    )

# The route for the profile pages
@app.route('/profile/<user_id>', methods=['GET'])
def profiles(user_id):

    user_page = get_user(user_id)

    # Checks if the user exists
    if user_page:
        user = get_logged_in_user()

        # Checks if the logged in user is the user
        if user and user.user_id == user_page.user_id:
            return redirect('/profile')

        if user_page.coach:

            # Gets the swimmers of the coach
            school_id = user_page.school_id
            swimmers = map(User, db.get_students(school_id))

            return render_template(
                'coachprofile.html',
                main=False,
                user=user,
                user_page=user_page,
                swimmers=swimmers,
                active_gala=False,
                live_gala=False
            )

        return render_template(
            'profile.html',
            main=False,
            user=user,
            user_page=user_page,
            active_gala=False,
            live_gala=False
    )

    return 'Invalid user id'

# The route for the profile pictures
@app.route('/profile/<user_id>/picture', methods=['GET'])
def profile_picture(user_id):

    user = get_user(user_id)

    # Sends the profile picture if the user has one
    if user.has_picture:
        filename = 'app/profile_pictures/' + user_id
        file = open(filename, 'rb')
        return send_file(file, mime.from_file(filename))

    # Sends the default profile picture if the user is a coach
    if user.coach:
        filename = 'app/profile_pictures/coach.png'
        file = open(filename, 'rb')
        return send_file(file, 'png')

    # Sends the default profile picture if the user is a student
    if not user.coach:
        filename = 'app/profile_pictures/swimmer.png'
        file = open(filename, 'rb')
        return send_file(file, 'png')

# The route for the upload picture method
@app.route('/profile/<user_id>/upload_picture', methods=['POST'])
def upload_profile_picture(user_id):

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user_page = get_user(user_id)
    user = get_user(db.get_user_id(token))

    # Checks if the user is allowed to edit the profile picture
    if not user.is_owner(user_page):
        return 'You do not have permission to do this', 403

    # Checks if the file has been provided
    if 'file' in request.files:

        # Gets the file from the form
        file = request.files['file']

        # Checks if the file is valid
        if file.filename == '':
            return 'No file was selected', 400

        # Checks if the file is an image
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return 'File must be an image', 400

        # Saves the file
        file.save('app/profile_pictures/' + str(user_id))

        # Updates the database
        db.update_picture(user_id, True)

        # Returns a link to the profile picture
        return f'/profile/{user_id}/picture' , 200

    return 'File was not provided', 400

# The route for the remove picture method
@app.route('/profile/<user_id>/remove_picture', methods=['POST'])
def remove_profile_picture(user_id):

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user_page = get_user(user_id)
    user = get_user(db.get_user_id(token))

    # Checks if the user is allowed to edit the profile picture
    if not user.is_owner(user_page):
        return 'You do not have permission to do this', 403

    # Removes the file
    filename = 'app/profile_pictures/' + str(user_id)
    if os.path.exists(filename):
        os.remove(filename)

    # Updates the database
    db.update_picture(user_id, False)

    # Returns a link to the profile picture
    return f'/profile/{user_id}/picture', 200


# The route for the update user details method
@app.route('/profile/<user_id>/update', methods=['POST'])
def update_details(user_id):

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user_page = get_user(user_id)
    user = get_user(db.get_user_id(token))

    # Checks if the user is allowed to edit the profile picture
    if not user.is_owner(user_page):
        return 'You do not have permission to do this', 403

    # Updates the user's favourite stroke
    if 'fav_stroke' in request.form:
        fav_stroke = request.form['fav_stroke'].lower()
        if fav_stroke not in STROKES:
            return 'Invalid stroke', 400
        db.update_fav_stroke(user_id, fav_stroke)

    # Updates the user's swimming status
    if 'swimming' in request.form:
        db.update_is_swimming(user_id, True)
    else:
        db.update_is_swimming(user_id, False)

    return redirect(f'/profile/{user_id}')


# Checks to see if the current file is the one being run (ie if another file
# called it then the app should have been run already, this file should on be run
# by itself for debugging)
if __name__ == '__main__':

    # Runs the app with debugging
    app.run(debug=True, use_reloader=False)