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

    @property
    def admin(self):
        return self.coach or self.captain

    def can_edit(self, page):
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

        self.date = details[2]
        self.status = details[3]

        self.school_ids = db.get_gala_schools(self.id)
        self.schools = list(map(School, map(db.get_school, self.school_ids)))

    @property
    def competitors(self):
        names = map(lambda school: school.name, self.schools)
        return ' vs '.join(names)

class Lane:

    def __init__(self, details):

        self.id = details[0]
        self.gala = Gala(db.get_gala(details[1]))

        self.number = details[2]

        self.volunteer = db.get_volunteer(self.id)
        if self.volunteer:
            self.volunteer = Volunteer(self.volunteer)

class Event:

    def __init__(self, details):

        self.id = details[0]
        self.gala = Gala(db.get_gala(details[1]))

        self.number = details[2]
        self.heats = details[3]
        self.age_range = details[4]
        self.gender = details[5]
        self.parts = details[6]
        self.relay = details[7]
        self.length = details[8]
        self.stroke = details[9]
        self.live = details[10]

        self.races = list(map(Race, db.get_races(self.id)))

    @property
    def name(self):
        # Format the name of the event
        age_range = f'{self.age_range} ' if self.age_range != 'all' else ''
        parts = f'{self.parts}x' if self.parts > 1 else ''
        return f'{age_range}{self.gender.capitalize()} {parts}{self.length}m {self.stroke.capitalize()}'

    @property
    def status(self):
        if self.live:
            return 1
        for race in self.races:
            if race.time:
                return 2
        return 0

    def can_swim(self, user):
        if user.gender == 'male' and self.gender == 'boys':
            return True
        if user.gender == 'female' and self.gender == 'girls':
            return True
        if self.gender == 'mixed':
            return True
        return False

    def lane_participant(self, lane, swimmer):
        for race in self.races:
            # Checks if the event and lane match the race
            if self.id == race.event_id and lane.id == race.lane_id:
                # Checks if the swimmer is in the matched race
                if swimmer.id in race.participant_ids:
                    return True
        return False

    def list_races(self, lanes):
        for lane in lanes:
            for race in self.races:
                # Checks if there is a race in the event for the lane
                if race.lane_id == lane.id:
                    # Yields the lane and race back so it can be looped over
                    yield lane, race
                    break

class Race:

    def __init__(self, details):

        self.id = details[0]
        self.lane_id = details[1]
        self.event_id = details[2]

        self.heat = details[3]
        self.time = details[4]

        self.participant_ids = list(map(lambda x: x[0], db.get_participants(self.id)))
        self.participants = list(map(User, map(db.get_user, self.participant_ids)))

    def swimmer_names(self):
        names = list()
        for participant in self.participants:
            names.append(f'{participant.name} {participant.surname}')
        return ', '.join(names)

class Volunteer:

    def __init__(self, details):
        self.id = details[0]
        self.lane_id = details[1]
        self.email = details[2]
        self.code = details[3]

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
        status=db.get_gala_status()
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
            status=db.get_gala_status()
        )

    return render_template(
        'profile.html',
        main=False,
        user=user,
        user_page=user,
        status=db.get_gala_status()
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
                status=db.get_gala_status()
            )

        return render_template(
            'profile.html',
            main=False,
            user=user,
            user_page=user_page,
            status=db.get_gala_status()
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

    # Checks if there is already an active gala
    if db.get_gala_status():
        return redirect('/manage')

    # Gets the list of schools
    schools = list(map(School, db.get_other_schools(user.school.id)))

    return render_template(
        'creategala.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        schools=schools
    )

# The route for the create gala method
@app.route('/create', methods=['POST'])
def create_gala_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    # Checks to see if there is a current gala on
    status = db.get_gala_status()
    if status == 1:
        return redirect('/manage')
    elif status == 2:
        return redirect('/manage_live')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is a coach
    if not user.coach:
        return 'You do not have permission to do this', 403

    # Checks if there is already an active gala
    if db.get_gala_status():
        return 'There is already an active gala', 400

    # Checks if the user has provided schools
    if 'schools' not in request.form:
        return 'Schools not provided', 400
    schools = request.form['schools']

    # Checks if the user has provided schools as a list
    if type(schools) == str:
        schools = [schools]

    # Checks if the schools are valid
    for school_id in schools:
        if not db.get_school(school_id):
            return 'Invalid school', 400

    # Checks if the user has provided a host_id
    if 'host' not in request.form:
        return 'Host not provided', 400
    host_id = request.form['host']

    # Checks if the host is valid
    if not db.get_school(host_id):
        return 'Invalid host', 400

    # Checks if the user has provided a date
    if 'date' not in request.form:
        return 'Date not provided', 400
    date = request.form['date']

    # Adds the gala to the database
    db.add_gala(host_id, date)
    gala = Gala(db.get_upcoming_gala())

    # Adds the schools to the gala
    db.add_gala_school(gala.id, user.school.id)
    for school_id in schools:
        db.add_gala_school(gala.id, school_id)

    # Redirects to the manage page
    return redirect('/manage')

# The route for the manage page
@app.route('/manage', methods=['GET'])
def manage():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    # Checks to see if there is a current gala on
    status = db.get_gala_status()
    if status == 0:
        return redirect('/')
    elif status == 2:
        return redirect('/manage_live')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    gala = Gala(db.get_upcoming_gala())
    schools = map(School, db.get_other_schools(user.school.id))
    lanes = list(map(Lane, db.get_lanes(gala.id)))
    events = list(map(Event, db.get_events(gala.id)))
    swimmers = list(map(User, db.get_swimmers(user.school.id)))

    return render_template(
        'managegala.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        gala=gala,
        schools=schools,
        lanes=lanes,
        events=events,
        swimmers=swimmers
    )

# The route for the update gala method
@app.route('/update_gala', methods=['POST'])
def update_gala_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided a school
    if 'schools' not in request.form:
        return 'Schools not provided', 400
    schools = request.form['schools'].split(',')

    # Checks if the schools are valid
    for school_id in schools:
        if not db.get_school(int(school_id)):
            return 'Invalid school', 400

    # Checks if the user has provided a host_id
    if 'host' not in request.form:
        return 'Host not provided', 400
    host_id = request.form['host']

    # Checks if the host is valid
    if not db.get_school(host_id):
        return 'Invalid host', 400

    # Checks if the user has provided a date
    if 'date' not in request.form:
        return 'Date not provided', 400
    date = request.form['date']

    # Gets the gala_id
    gala_id = db.get_upcoming_gala()[0]

    # Updates the gala in the database
    db.update_gala(gala_id, host_id, date)

    # Removes the schools from the gala
    gala_schools = db.get_gala_schools(gala_id)
    for school_id in gala_schools:
        if school_id != user.school.id and school_id not in schools:
            db.remove_gala_school(gala_id, school_id)

    # Adds the schools to the gala
    for school_id in schools:
        if school_id not in gala_schools:
            db.add_gala_school(gala_id, school_id)

    return 'ok'

# The route for the add lane method
@app.route('/add_lane', methods=['POST'])
def add_lane_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided a lane
    if 'lane' not in request.form:
        return 'Lane not provided', 400
    lane = request.form['lane']

    gala = Gala(db.get_upcoming_gala())

    # Adds the lane to the gala and then gets the lane id
    db.add_lane(gala.id, lane)
    lane_id = db.get_lane(gala.id, lane)[0]

    # Returns the lane id
    return {'lane_id': lane_id}

# The route for the update lanes method
@app.route('/update_lanes', methods=['POST'])
def update_lanes_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided a list of lane_ids and lane_nos
    if 'lanes' not in request.form:
        return 'Lanes not provided', 400
    lanes = request.form['lanes']

    # Converts the str to a list
    lanes = lanes[2:-2].split('],[')
    lanes = list(map(lambda x: x.split(','), lanes))

    # Updates the lanes
    gala_id = db.get_upcoming_gala()[0]
    db.update_lanes(gala_id, lanes)

    return 'ok'

# The route for the add event method
@app.route('/add_event', methods=['POST'])
def add_event_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an coach
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided a stroke
    if 'stroke' not in request.form:
        return 'Stroke not provided', 400
    stroke = request.form['stroke']

    # Checks if the user has provided the number of parts
    if 'parts' not in request.form:
        return 'Parts not provided', 400
    parts = request.form['parts']

    # Checks if the user has provided the length
    if 'length' not in request.form:
        return 'Length not provided', 400
    length = request.form['length']

    # Checks if the user has provided the age group
    if 'age_group' not in request.form:
        return 'Age group not provided', 400
    age_group = request.form['age_group']

    # Checks if the user has provided the group
    if 'group' not in request.form:
        return 'Group not provided', 400
    group = request.form['group']

    # Checks if the coach has provided a relay status
    relay = 'relay' in request.form

    gala_id = db.get_upcoming_gala()[0]
    event_no = len(db.get_events(gala_id)) + 1

    # Adds the event to the gala and then gets the event id
    db.add_event(gala_id, event_no, age_group, group, parts, relay, length, stroke)
    event_id = db.get_event(gala_id, event_no)[0]

    # Returns the event id
    return {'event_id': event_id}

# The route for the update events method
@app.route('/update_events', methods=['POST'])
def update_events_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided a list of event_ids and event_nos
    if 'events' not in request.form:
        return 'Events not provided', 400
    events = request.form['events']

    # Converts the str to a list
    events = events[1:-1].split(',')

    # Updates the events
    gala_id = db.get_upcoming_gala()[0]
    db.update_events(gala_id, events)

    return 'ok'

# The route for the update race method
@app.route('/update_race', methods=['POST'])
def update_race_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided the event id
    if 'event_id' not in request.form:
        return 'Event id not provided', 400
    event_id = request.form['event_id']

    # Checks if the user has provided the lane id
    if 'lane_id' not in request.form:
        return 'Lane id not provided', 400
    lane_id = request.form['lane_id']

    # Checks if the user has provided a list of swimmer_ids
    if 'swimmer_ids' not in request.form:
        return 'Swimmer ids not provided', 400
    swimmer_ids = request.form['swimmer_ids'].split(',')

    if swimmer_ids == ['null'] or swimmer_ids == ['']:
        swimmer_ids = list()

    # Gets the race or creates it if it doesn't exist
    race = db.get_race(event_id, lane_id, heat=1)
    if not race and swimmer_ids:
        db.add_race(event_id, lane_id, heat=1)
        race = db.get_race(event_id, lane_id, heat=1)
    elif not race and not swimmer_ids:
        return 'ok'

    # Updates the race participants
    db.update_participants(race[0], swimmer_ids)

    # Removes the race if there are no participants
    if not swimmer_ids:
        db.remove_race(event_id, lane_id, heat=1)

    return 'ok'

# The route for the current gala page
@app.route('/current', methods=['GET'])
def current_gala_page():

    # Checks to see if there is a current gala on
    status = db.get_gala_status()
    if status == 0:
        return redirect('/')
    elif status == 2:
        return redirect('/live')

    # Assumes that the user is here for Rugby's gala
    school_id = 1

    gala = Gala(db.get_upcoming_gala())
    schools = map(School, db.get_other_schools(school_id))
    lanes = list(map(Lane, db.get_lanes(gala.id)))
    events = list(map(Event, db.get_events(gala.id)))
    swimmers = list(map(User, db.get_swimmers(school_id)))

    return render_template(
        'currentgala.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        gala=gala,
        schools=schools,
        lanes=lanes,
        events=events,
        swimmers=swimmers
    )

# The route for the get swimmers method
@app.route('/get_swimmers', methods=['POST'])
def get_swimmers_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided the event id
    if 'event_id' not in request.form:
        return 'Event id not provided', 400
    event_id = request.form['event_id']


    swimmers = list(map(User, db.get_swimmers(user.school.id)))
    event = Event(db.get_event_by_id(event_id))

    event_swimmers = list()
    for swimmer in swimmers:
        if event.can_swim(swimmer):
            # Adds the swimmer's id, name and if the event is their favourite
            name = swimmer.name + ' ' + swimmer.surname
            fav_stroke = swimmer.fav_stroke == event.stroke
            event_swimmers.append([swimmer.id, name, fav_stroke])

    return event_swimmers

# The route for the make gala live method
@app.route('/make_live/<gala_id>', methods=['GET'])
def make_gala_live_method(gala_id):

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the gala is currently being set up
    status = db.get_gala_status()
    if status != 1:
        return 'Gala is not currently being set up', 400

    # Makes the gala live
    db.update_gala_status(gala_id, 2)

    return redirect('/manage_live')

# The route for the manage live gala page
@app.route('/manage_live', methods=['GET'])
def manage_live_gala_page():

    # Checks to see if there is a current gala on
    status = db.get_gala_status()
    if status == 0:
        return redirect('/')
    elif status == 1:
        return redirect('/manage')

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    gala = Gala(db.get_upcoming_gala())
    school_ids = db.get_gala_schools(gala.id)
    schools = map(School, map(db.get_school, school_ids))
    lanes = list(map(Lane, db.get_lanes(gala.id)))
    events = list(map(Event, db.get_events(gala.id)))

    return render_template(
        'managelive.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        gala=gala,
        schools=schools,
        lanes=lanes,
        events=events
    )

# The route for the make gala active method
@app.route('/make_active/<gala_id>', methods=['GET'])
def make_gala_active_method(gala_id):

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the gala is currently live
    status = db.get_gala_status()
    if status != 2:
        return 'Gala is not currently live', 400

    # Makes the gala active
    db.update_gala_status(gala_id, 1)

    return redirect('/manage')

# The route for the update event status method
@app.route('/update_event_status', methods=['POST'])
def update_event_status_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided the event id
    if 'event_id' not in request.form:
        return 'Event id not provided', 400
    event_id = request.form['event_id']

    # Checks if the user has provided the heat
    if 'heat' not in request.form:
        return 'Heat not provided', 400
    heat = request.form['heat']

    # Checks if the user has provided the current status
    if 'status' not in request.form:
        return 'Status not provided', 400
    status = int(request.form['status'])

    gala = Gala(db.get_upcoming_gala())

    if status in [0, 2]:

        # Checks if there are any live events
        for event in map(Event, db.get_events(gala.id)):
            if event.live != 0:
                return 'There is already a live event', 400

        # Update the event status
        db.update_event_live(event_id, heat)
        return {'status': 1}

    db.update_event_live(event_id, 0)
    event = Event(db.get_event_by_id(event_id))

    # Returns the status of the event
    return {'status': event.status}

# The route for the manage live gala page
@app.route('/live', methods=['GET'])
def live_gala_page():

    # Checks to see if there is a current gala on
    status = db.get_gala_status()
    if status == 0:
        return redirect('/')
    elif status == 1:
        return redirect('/current')

    gala = Gala(db.get_upcoming_gala())
    school_ids = db.get_gala_schools(gala.id)
    schools = map(School, map(db.get_school, school_ids))
    lanes = list(map(Lane, db.get_lanes(gala.id)))
    events = list(map(Event, db.get_events(gala.id)))

    return render_template(
        'livegala.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        gala=gala,
        schools=schools,
        lanes=lanes,
        events=events
    )

# The route for the end gala method
@app.route('/end_gala/<gala_id>', methods=['GET'])
def end_gala_method(gala_id):

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the gala is currently live
    status = db.get_gala_status()
    if status != 2:
        return 'Gala is not currently live', 400

    # Ends the gala
    db.update_gala_status(gala_id, 0)

    return redirect('/gala/' + gala_id)

# The route for the past galas page
@app.route('/galas', methods=['GET'])
def past_galas_page():

    # Assumes that the user is here for Rugby's gala
    school_id = 1

    gala_ids = map(lambda x: x[0], db.get_galas(school_id))
    galas = map(Gala, map(db.get_gala, gala_ids))

    return render_template(
        'pastgalas.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        galas=galas
    )

# The route for the gala page
@app.route('/gala/<gala_id>', methods=['GET'])
def gala_page(gala_id):

    gala = Gala(db.get_gala(gala_id))
    school_ids = db.get_gala_schools(gala_id)
    schools = map(School, map(db.get_school, school_ids))
    lanes = list(map(Lane, db.get_lanes(gala_id)))
    events = list(map(Event, db.get_events(gala_id)))

    return render_template(
        'gala.html',
        main=False,
        user=get_logged_in_user(),
        status=db.get_gala_status(),
        gala=gala,
        schools=schools,
        lanes=lanes,
        events=events
    )

# The route for the update volunteer method
@app.route('/update_volunteer', methods=['POST'])
def update_volunteer_method():

    # Checks if the user is logged in
    if not check_token():
        return redirect('/login')

    token = request.cookies['token']
    user = get_user(db.get_user_id(token))

    # Checks if the user is an admin
    if not user.admin:
        return 'You do not have permission to do this', 403

    # Checks if the user has provided the lane id
    if 'lane_id' not in request.form:
        return 'Lane id not provided', 400
    lane_id = request.form['lane_id']

    # Checks if the user has provided the volunteer email
    if 'email' not in request.form:
        return 'Volunteer email not provided', 400
    email = request.form['email']

    volunteer = db.get_volunteer(lane_id)
    if volunteer:
        volunteer = Volunteer(volunteer)
        db.remove_volunteer(lane_id)

        SUBJECT = 'Volunteering'
        TEXT = 'You have been removed as a volunteer from the upcoming gala.'

        # Prepares the actual message
        message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format(config['email'], volunteer.email, SUBJECT, TEXT)
        server.sendmail(config['email'], volunteer.email, message)

    if not email:
        return 'ok'

    db.add_volunteer(lane_id, email)
    volunteer = Volunteer(db.get_volunteer(lane_id))

    SUBJECT = 'Volunteering'
    TEXT = (
        'You have been invited to volunteer at the upcoming gala. '
        'Please use the following link to record the results:\n\n'
        'https://www.rugbygala.com/volunteer/' + volunteer.id +
        '/' + volunteer.code
    )

    # Prepares the actual message
    message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format(config['email'], email, SUBJECT, TEXT)
    server.sendmail(config['email'], email, message)

    return 'ok'

# Checks to see if the current file is the one being run (ie if another file
# called it then the app should have been run already, this file should on be run
# by itself for debugging)
if __name__ == '__main__':

    # Runs the app with debugging
    app.run(debug=True, use_reloader=False)