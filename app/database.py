import sqlite3
import os
import time

# Imports the bcrypt module for hashing passwords
import bcrypt

# Imports the secrets module for generating random tokens
import secrets


# The database object which will handle SQL queries
class Database:

    # Upon calling the Database object '__init__' will initialise the object
    def __init__(self, path):

        # Checks if the database exists
        if not os.path.exists(path):
            # Creates a new database and populates it with tables
            self.create(path)
        else:
            # The connect function returns an SQLite3 Connection object
            # for querying the database
            # Check same thread allows for multiple processes to access
            # the database using the same connection object
            self.conn = sqlite3.connect(path, check_same_thread=False)

    def create(self, path):

        self.conn = sqlite3.connect(path, check_same_thread=False)

        # The cursor function returns an SQLite3 Cursor object which can be
        # used to execute SQL commands
        c = self.conn.cursor()

        # The cursor object's execute function will execute SQL commands to create
        # tables for the database
        c.execute("""
            CREATE TABLE School (
                school_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name     TEXT    NOT NULL
            );
        """)

        c.execute("""
            CREATE TABLE User (
                user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id       INTEGER NOT NULL,

                email           TEXT    NOT NULL,
                hash            TEXT    NOT NULL,
                name            TEXT    NOT NULL,
                surname         TEXT    NOT NULL,
                gender          TEXT    NOT NULL,
                has_picture     INTEGER NOT NULL,
                is_coach        INTEGER NOT NULL,

                FOREIGN KEY (school_id) REFERENCES School (school_id)
            );
        """)

        c.execute("""
            CREATE TABLE Gala (
                gala_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id         INTEGER NOT NULL,

                date            TEXT    NOT NULL,
	            status          INTEGER NOT NULL,

	            FOREIGN KEY (host_id) REFERENCES School (school_id)
            );
        """)

        c.execute("""
            CREATE TABLE Gala_School (
                gala_id         INTEGER NOT NULL,
                school_id       INTEGER NOT NULL,

                host            TEXT    NOT NULL,

                PRIMARY KEY (gala_id, school_id),
                FOREIGN KEY (gala_id) REFERENCES Gala (gala_id),
                FOREIGN KEY (school_id) REFERENCES School (school_id)
            );
        """)

        c.execute("""
            CREATE TABLE Token (
                token_id        TEXT   PRIMARY KEY,
                user_id         INTEGER NOT NULL,
                expiry          INTEGER NOT NULL,

                FOREIGN KEY (user_id) REFERENCES User (user_id)
            );
        """)

        c.execute("""
            CREATE TABLE Student (
                user_id         INTEGER NOT NULL,

                graduation_year INTEGER NOT NULL,
                fav_stroke      TEXT    NOT NULL,
                is_captain      INTEGER NOT NULL,
                is_swimming     INTEGER NOT NULL,

                FOREIGN KEY (user_id) REFERENCES User (user_id)
            );
        """)

        c.execute("""
            CREATE TABLE Lane (
                lane_id         INTEGER  PRIMARY KEY AUTOINCREMENT,
                gala_id         INTEGER  NOT NULL,

                lane_no         INTEGER  NOT NULL,

                FOREIGN KEY (gala_id) REFERENCES Gala (gala_id)
            );
        """)

        c.execute("""
            CREATE TABLE Volunteer (
                volunteer_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                lane_id         INTEGER NOT NULL,

                email           TEXT    NOT NULL,
                code            TEXT    NOT NULL,

                FOREIGN KEY (lane_id) REFERENCES Lane (lane_id)
            );
        """)

        c.execute("""
            CREATE TABLE Event (
                event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                gala_id         INTEGER NOT NULL,

                event_no        INTEGER NOT NULL,
                heats           INTEGER NOT NULL,

                age_range       TEXT    NOT NULL,
                gender          TEXT    NOT NULL,
                parts           INTEGER NOT NULL,
                is_relay        INTEGER NOT NULL,
                length          INTEGER NOT NULL,
                stroke          TEXT    NOT NULL,
                is_live         INTEGER NOT NULL,

                FOREIGN KEY (gala_id) REFERENCES Gala (gala_id)
            );
        """)

        c.execute("""
            CREATE TABLE Race (
                race_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                lane_id         INTEGER NOT NULL,
                event_id        INTEGER NOT NULL,

                heat            INTEGER NOT NULL,
                time            INTEGER NULL,

                FOREIGN KEY (lane_id) REFERENCES Lane (lane_id),
                FOREIGN KEY (event_id) REFERENCES Event (event_id)
            );
        """)

        c.execute("""
            CREATE TABLE Participant (
                user_id         INTEGER NOT NULL,
                race_id         INTEGER NOT NULL,

                PRIMARY KEY (user_id, race_id),
                FOREIGN KEY (user_id) REFERENCES User (user_id),
                FOREIGN KEY (race_id) REFERENCES Race (race_id)
            );
        """)

        # Commits the changes to the database
        self.conn.commit()

    # Gets the user_id from the email
    def get_user_id_from_email(self, email):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the user_id of the email
        c.execute("""
            SELECT user_id
            FROM User
            WHERE email = ?
        """, (email,))
        result = c.fetchone()

        if result is None:
            return None

        return result[0]

    # Checks if the email exists
    def used_email(self, email):
        return self.get_user_id_from_email(email) is not None

    # Checks if the email and password are valid
    def check_password(self, email, password):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the hash of the user with the given email
        c.execute("""
            SELECT hash
            FROM User
            WHERE email = ?
        """, (email,))
        hash = c.fetchone()[0]

        # Encodes the password and hash to utf-8
        password = password.encode('utf-8')
        if isinstance(hash, str):
            hash = hash.encode('utf-8')

        # Checks if the password matches the hash
        return bcrypt.checkpw(password, hash)

    # Generates a token so the user can stay logged in
    def generate_token(self, email, expiry):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the user_id of the email
        user_id = self.get_user_id_from_email(email)

        # Generates a random token
        token = secrets.token_urlsafe(16)
        # Gets the current time and adds the expiry time
        expiry = int(time.time()) + expiry

        # Inserts the token into the database
        c.execute("""
            INSERT INTO Token (token_id, user_id, expiry)
            VALUES (?, ?, ?)
        """, (token, user_id, expiry))
        self.conn.commit()

        return token

    # Checks if the token is valid
    def check_token(self, token):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the expiry time of the token
        c.execute("""
            SELECT expiry
            FROM Token
            WHERE token_id = ?
        """, (token,))

        # Checks if the token exists
        expiry = c.fetchone()
        if expiry is None:
            return False
        expiry = expiry[0]

        # Checks if the token has expired
        if expiry < int(time.time()):

            # Deletes the token from the database
            c.execute("""
                DELETE FROM Token
                WHERE token_id = ?
            """, (token,))
            self.conn.commit()

            return False

        return True

    # Gets the user_id from the token
    def get_user_id(self, token):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the user_id of the token
        c.execute("""
            SELECT user_id
            FROM Token
            WHERE token_id = ?
        """, (token,))
        user_id = c.fetchone()[0]

        return user_id

    # Gets all the user details from the user_id
    def get_user(self, user_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the user details from the user_id
        c.execute("""
            SELECT *
            FROM User
            WHERE user_id = ?
        """, (user_id,))
        user = c.fetchone()

        return user

    # Gets all the student details from the user_id
    def get_student(self, user_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the student details from the user_id
        c.execute("""
            SELECT *
            FROM Student
            WHERE user_id = ?
        """, (user_id,))
        student = c.fetchone()

        return student

    # Sets the profile picture of the user
    def update_picture(self, user_id, value):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Updates the profile picture of the user
        c.execute("""
            UPDATE User
            SET has_picture = ?
            WHERE user_id = ?
        """, (int(value), user_id))
        self.conn.commit()

    def update_fav_stroke(self, user_id, value):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Updates the favorite stroke of the user
        c.execute("""
            UPDATE Student
            SET fav_stroke = ?
            WHERE user_id = ?
        """, (value, user_id))
        self.conn.commit()

    def update_is_swimming(self, user_id, value):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Updates the is swimming of the user
        c.execute("""
            UPDATE Student
            SET is_swimming = ?
            WHERE user_id = ?
        """, (int(value), user_id))
        self.conn.commit()

    def get_students(self, school_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets all students from a school
        c.execute("""
            SELECT *
            FROM User
            WHERE school_id = ?
            AND is_coach = 0
        """, (school_id,))
        students = c.fetchall()

        return students

    def add_student(self, school_id, email, name, surname, gender, graduation_year, fav_stroke, is_captain, is_swimming):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Generates a random password
        password = secrets.token_urlsafe(16)
        # Hashes the password
        hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Inserts the user into the database
        c.execute("""
            INSERT INTO User (school_id, email, hash, name, surname,
                gender, has_picture, is_coach)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """, (school_id, email, hash, name, surname, gender))
        self.conn.commit()

        # Gets the user_id of the user
        c.execute("""
            SELECT user_id
            FROM User
            WHERE email = ?
        """, (email,))

        user_id = c.fetchone()[0]

        # Inserts the student into the database
        c.execute("""
            INSERT INTO Student (user_id, graduation_year, fav_stroke,
            is_captain, is_swimming)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, graduation_year, fav_stroke, int(is_captain), int(is_swimming)))
        self.conn.commit()

    def update_password(self, user_id, password):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Hashes the password
        hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Updates the password of the user
        c.execute("""
            UPDATE User
            SET hash = '?'
            WHERE user_id = ?
        """, (hash, user_id))
        self.conn.commit()

    def get_other_schools(self, school_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets all schools except the current school
        c.execute("""
            SELECT *
            FROM School
            WHERE school_id != ?
        """, (school_id,))
        schools = c.fetchall()

        return schools

    def add_gala(self, host_id, date):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Inserts the gala into the database
        c.execute("""
            INSERT INTO Gala (
                host_id, date, status)
            VALUES (?, ?, 1)
        """, (host_id, date))
        self.conn.commit()

    def add_gala_school(self, gala_id, school_id):

            # Creates a cursor object to execute SQL commands
            c = self.conn.cursor()

            # Inserts the gala into the database
            c.execute("""
                INSERT INTO Gala_School (
                    gala_id, school_id)
                VALUES (?, ?)
            """, (gala_id, school_id))
            self.conn.commit()

    def get_school(self, school_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Checks if the school exists
        c.execute("""
            SELECT *
            FROM School
            WHERE school_id = ?
        """, (school_id,))
        return c.fetchone()

    def get_gala(self, gala_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Checks if the gala exists
        c.execute("""
            SELECT *
            FROM Gala
            WHERE gala_id = ?
        """, (gala_id,))
        return c.fetchone()

    def get_upcoming_gala(self):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the current gala
        c.execute("""
            SELECT *
            FROM Gala
            WHERE status = 1 OR status = 2
            ORDER BY date DESC
        """)
        return c.fetchone()

    def get_gala_schools(self, gala_id):

            # Creates a cursor object to execute SQL commands
            c = self.conn.cursor()

            # Gets the current gala
            c.execute("""
                SELECT school_id
                FROM Gala_School
                WHERE gala_id = ?
            """, (gala_id,))
            return [x[0] for x in c.fetchall()]

    def get_gala_status(self):

        gala = self.get_upcoming_gala()

        if gala is None:
            return 0
        return gala[3]

    def update_gala(self, gala_id, host_id, date):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Updates the gala
        c.execute("""
            UPDATE Gala
            SET host_id = ?, date = ?
            WHERE gala_id = ?
        """, (host_id, date, gala_id))
        self.conn.commit()

    def remove_gala_school(self, gala_id, school_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Removes the gala school
        c.execute("""
            DELETE FROM Gala_School
            WHERE gala_id = ? AND school_id = ?
        """, (gala_id, school_id))
        self.conn.commit()

    def add_lane(self, gala_id, lane):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Inserts the lane into the database
        c.execute("""
            INSERT INTO Lane (
                gala_id, lane_no)
            VALUES (?, ?)
        """, (gala_id, lane))
        self.conn.commit()

    def get_lane(self, gala_id, lane):

            # Creates a cursor object to execute SQL commands
            c = self.conn.cursor()

            # Gets the lane
            c.execute("""
                SELECT *
                FROM Lane
                WHERE gala_id = ? AND lane_no = ?
            """, (gala_id, lane))
            return c.fetchone()

    def get_lanes(self, gala_id):

            # Creates a cursor object to execute SQL commands
            c = self.conn.cursor()

            # Gets the lane
            c.execute("""
                SELECT *
                FROM Lane
                WHERE gala_id = ?
                ORDER BY lane_no
            """, (gala_id,))
            return c.fetchall()

    def update_lanes(self, gala_id, lanes):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Deletes all lanes except the current ones
        c.execute(f"""
            DELETE FROM Lane
            WHERE gala_id = ? AND lane_id NOT IN ({','.join('?' * len(lanes))})
        """, (gala_id, *[x[0] for x in lanes]))

        print(lanes)

        if lanes[0] == ['']:
            self.conn.commit()
            return

        # Updates the lanes
        for lane in lanes:
            c.execute("""
                UPDATE Lane
                SET lane_no = ?
                WHERE gala_id = ? AND lane_id = ?
            """, (lane[1], gala_id, lane[0]))

        self.conn.commit()

    def get_events(self, gala_id):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the events
        c.execute("""
            SELECT *
            FROM Event
            WHERE gala_id = ?
            ORDER BY event_no
        """, (gala_id,))
        return c.fetchall()

    def get_event(self, gala_id, event_no):

            # Creates a cursor object to execute SQL commands
            c = self.conn.cursor()

            # Gets the event
            c.execute("""
                SELECT *
                FROM Event
                WHERE gala_id = ? AND event_no = ?
            """, (gala_id, event_no))
            return c.fetchone()

    def add_event(self, gala_id, event_no, age_range, gender, parts, is_relay, length, stroke):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Inserts the event into the database
        c.execute("""
            INSERT INTO Event (gala_id, event_no, heats, age_range, gender,
                parts, is_relay, length, stroke, is_live)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, 0)
        """, (gala_id, event_no, age_range, gender, parts, is_relay, length, stroke))

        self.conn.commit()

    def update_events(self, gala_id, events):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Deletes all events except the current ones
        c.execute(f"""
            DELETE FROM Event
            WHERE event_id NOT IN ({','.join('?' * len(events))})
        """, (*events,))

        # Updates the events
        for i, event in enumerate(events):
            c.execute("""
                UPDATE Event
                SET event_no = ?
                WHERE gala_id = ? AND event_id = ?
            """, (i + 1, gala_id, event))

        self.conn.commit()

# If database.py is the file being run
if __name__ == '__main__':
	# Creates a database called test.db
	database = Database('test.db')