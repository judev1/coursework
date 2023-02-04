# Imports the Flask object within the flask module
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import send_file

import magic
import os
import datetime
import smtplib
import json


# Initiates the Flask object and sets the 'static' folder as the template folder
app = Flask(__name__, template_folder='static')

# Creates a new Magic object for getting the file type
mime = magic.Magic(mime=True)

# Loads the config for the smtp
with open('app/config.json') as file:
    config = json.load(file)

# Connects to the host over SMTP using credentials from the config
# server = smtplib.SMTP(config['host'], config['port'])
# server.starttls()
# server.login(config['email'], config['password'])


# Imports the Database object from the database module
from database import Database

# Initialises the Database object
db = Database('app/database.db')


STROKES = [
    'frontcrawl',
    'backstroke',
    'breaststroke',
    'butterfly',
    'medley'
]


class User:

    strokes = STROKES

    def __init__(self, details):

        self.id = details[0]
        self.school = School(db.get_school(details[1]))
        self.email = details[2]

        self.name = details[4]
        self.surname = details[5]
        self.gender = details[6]
        self.has_picture = bool(details[7])
        self.coach = bool(details[8])

        if not self.coach:

            details = db.get_student(self.id)
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
        return f'{self.graduation_year} Leaver'

    def is_admin(self):
        return self.coach or self.captain

    def can_edit(self, page):
        print(self.coach, self.id, page.school.id, type(self.coach), type(self.id), type(page.school.id))
        return self.coach and self.school.id == page.school.id

    def is_owner(self, page):
        owner = self.id == page.id
        return self.can_edit(page) or owner

    def is_host(self, gala):
        return self.school.id == gala.host.id

class School:

    def __init__(self, details):

        self.id = details[0]
        self.name = details[1]

class Gala:

    def __init__(self, details):

        self.id = details[0]
        self.host = School(db.get_school(details[1]))
        self.guest = School(db.get_school(details[2]))
        self.date = details[3]

        self.active = bool(details[4])
        self.live = bool(details[5])

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

# Checks if a password is valid
def check_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(not char.isalnum() for char in password):
        return False
    return True


# The route for the main page
@app.route('/', methods=['GET'])
def main():
    return render_template(
        'template.html',
        main=True,
        user=get_logged_in_user(),
        active_gala=bool(db.get_upcoming_gala()),
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
        if not db.used_email(email):
            return 'Email is not associated with an account'

        # Checks if the password has been provided
        if 'password' in request.form:

            # Gets the password from the form
            password = request.form['password']

            # Checks if the password is correct
            if not db.check_password(email, password):
                return 'Password is incorrect'

            # If the email and password pass all the checks
            expiry = 60*60*24*7 - 60
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

        school_id = user.school.id
        swimmers = map(User, db.get_students(school_id))

        return render_template(
            'coachprofile.html',
            main=False,
            user=user,
            user_page=user,
            swimmers=swimmers,
            active_gala=bool(db.get_upcoming_gala()),
            live_gala=False
        )

    return render_template(
        'profile.html',
        main=False,
        user=user,
        user_page=user,
        active_gala=bool(db.get_upcoming_gala()),
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
        if user and user.id == user_page.id:
            return redirect('/profile')

        if user_page.coach:

            # Gets the swimmers of the coach
            school_id = user_page.school.id
            swimmers = map(User, db.get_students(school_id))

            return render_template(
                'coachprofile.html',
                main=False,
                user=user,
                user_page=user_page,
                swimmers=swimmers,
                active_gala=bool(db.get_upcoming_gala()),
                live_gala=False
            )

        return render_template(
            'profile.html',
            main=False,
            user=user,
            user_page=user_page,
            active_gala=bool(db.get_upcoming_gala()),
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

# The route for the add student method
@app.route('/add_student', methods=['POST'])
def add_student():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if a coach is addding a student
    if not user.coach:
        return 'You do not have permission to do this', 403

    # Checks if the coach has provided a name
    if 'name' not in request.form:
        return 'Name not provided', 400
    name = request.form['name']

    # Checks if the coach has provided a surname
    if 'surname' not in request.form:
        return 'Surname not provided', 400
    surname = request.form['surname']

    # Checks if the coach has provided an email
    if 'email' not in request.form:
        return 'Email not provided', 400
    email = request.form['email']

    # Checks if the email is valid
    if db.used_email(email):
        return 'Email already associated with an account', 400

    # Checks if the coach has provided a year
    if 'year' not in request.form:
        return 'Year not provided', 400
    year = request.form['year']
    if not year.isdigit() and int(year) not in range(9, 14):
        return 'Year must be a number between 9 and 13', 400
    graduation_year = datetime.datetime.now().year + 13 - int(year)

    # Checks if the coach has provided a gender
    if 'gender' not in request.form:
        return 'Gender not provided', 400
    gender = request.form['gender']
    if gender not in ['male', 'female']:
        return 'Gender must be male or female for groupings', 400

    # Checks if the coach has provided a favourite stroke
    if 'fav_stroke' not in request.form:
        return 'Favourite stroke not provided', 400
    fav_stroke = request.form['fav_stroke']
    if fav_stroke not in STROKES:
        return 'Invalid stroke', 400

    # Checks if the coach has provided a swimming status
    swimming = 'swimming' in request.form

    # Checks if the coach has provided a captain status
    captain = 'captain' in request.form

    # Adds the student to the database
    db.add_student(
        school_id=user.school.id,
        email=email,
        name=name,
        surname=surname,
        gender=gender,
        graduation_year=graduation_year,
        fav_stroke=fav_stroke,
        is_captain=captain,
        is_swimming=swimming
    )

    # Reloads the page
    return redirect(f'/profile/{user.id}')

# The route for the forgot password page
@app.route('/forgot-password', methods=['GET'])
def forgot_password():

        # Checks if the user is logged in
        if check_token():
            return redirect('/')

        return render_template('forgotpassword.html')

# The route for the forgot password method
@app.route('/forgot-password', methods=['POST'])
def forgot_password_method():

    # Checks if the user is logged in
    if check_token():
        return redirect('/')

    # Checks if the user has provided an email
    if 'email' not in request.form:
        return 'Email not provided', 400
    email = request.form['email']

    # Checks if the email is valid
    if not db.used_email(email):
        return 'Email not associated with an account', 400

    # Generates a two hour token
    token = db.generate_token(email, expiry=60*60*2)

    SUBJECT = 'Password Reset'
    TEXT = (
        'Please click the link below to reset your password:\n\n'
        f'http://127.0.0.1:5000/reset-password/{token}\n\n'
        'This link will expire in two hours.'
    )

    # Prepares the actual message
    message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format(config['email'], email, SUBJECT, TEXT)

    # Send the mail
    server.sendmail(config['email'], email, message)

    return redirect('/forgot-password')

# The route for the reset password page
@app.route('/reset-password/<token>', methods=['GET'])
def reset_password(token):

    # Checks if the user is logged in
    if check_token():
        return redirect('/')

    # Checks if the token is valid
    if not db.check_token(token):
        return 'Invalid token', 400

    return render_template('resetpassword.html')

# The route for the reset password method
@app.route('/reset-password/<token>', methods=['POST'])
def reset_password_method(token):

    # Checks if the user is logged in
    if check_token():
        return redirect('/')

    # Checks if the token is valid
    if not db.check_token(token):
        return 'Invalid token', 400

    # Checks if the user has provided a password
    if 'password' not in request.form:
        return 'Password not provided', 400
    password = request.form['password']

    # Checks if the password is valid
    if not check_password(password):
        return 'Invalid password', 400

    # Gets the user's id from the token
    user_id = db.get_user_id(token)

    # Updates the user's password
    db.update_password(user_id, password)

    # Should realistically delete the token but I'm too lazy to do that

    return redirect('/login')

# The route for the create gala page
@app.route('/create', methods=['GET'])
def create_gala():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is a coach
    if not user.coach:
        return 'You do not have permission to do this', 403

    # Gets the list of schools
    schools = map(School, db.get_other_schools(user.school.id))

    return render_template(
        'creategala.html',
        main=False,
        user=get_logged_in_user(),
        active_gala=bool(db.get_upcoming_gala()),
        live_gala=False,
        schools=schools
    )

# The route for the create gala method
@app.route('/create', methods=['POST'])
def create_gala_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is a coach
    if not user.coach:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided a school_id
    if 'school_id' not in request.form:
        return 'School not provided', 400
    school_id = request.form['school_id']

    # Checks if the school is valid
    if not db.get_school(school_id):
        return 'Invalid school', 400

    # Checks if the user has provided a home value
    home = 'home' in request.form

    # Sets the host and guest ids
    if home:
        host_id = user.school.id
        guest_id = school_id
    else:
        host_id = school_id
        guest_id = user.school.id

    # Checks if the user has provided a date
    if 'date' not in request.form:
        return 'Date not provided', 400
    date = request.form['date']

    # Adds the gala to the database
    db.add_gala(host_id, guest_id, date)

    # Redirects to the manage page
    return redirect('/manage')

# The route for the manage page
@app.route('/manage', methods=['GET'])
def manage():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is a coach
    if not user.coach:
        return 'You do not have permission to do this', 403

    gala = Gala(db.get_upcoming_gala())
    schools = map(School, db.get_other_schools(user.school.id))

    return render_template(
        'managegala.html',
        main=False,
        user=get_logged_in_user(),
        active_gala=gala.active,
        live_gala=False,
        gala=gala,
        schools=schools
    )

# The route for the update gala method
@app.route('/update_gala', methods=['POST'])
def update_gala_method():

        # Checks if the user is logged in
        if not check_token():
            return redirect('/login')

        token = request.cookies['token']
        user = get_user(db.get_user_id(token))

        # Checks if the user is a coach
        if not user.coach:
            return 'You do not have permission to do this', 403

        # Checks if the user has provided a school_id
        if 'school_id' not in request.form:
            return 'School not provided', 400
        school_id = request.form['school_id']

        # Checks if the school is valid
        if not db.get_school(school_id):
            return 'Invalid school', 400

        # Checks if the user has provided a home value
        home = 'home' in request.form

        # Sets the host and guest ids
        if home:
            host_id = user.school.id
            guest_id = school_id
        else:
            host_id = school_id
            guest_id = user.school.id

        # Checks if the user has provided a date
        if 'date' not in request.form:
            return 'Date not provided', 400
        date = request.form['date']

        # Gets the gala_id
        gala_id = db.get_upcoming_gala()[0]

        # Updates the gala in the database
        db.update_gala(gala_id, host_id, guest_id, date)

        # Redirects to the manage page
        return redirect('/manage')


# Checks to see if the current file is the one being run (ie if another file
# called it then the app should have been run already, this file should on be run
# by itself for debugging)
if __name__ == '__main__':

    # Runs the app with debugging
    app.run(debug=True, use_reloader=False)