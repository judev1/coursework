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
                home_school_id  INTEGER NOT NULL,
                guest_school_id INTEGER NOT NULL,

                date            TEXT    NOT NULL,
                is_active       INTEGER NOT NULL,
                is_live         INTEGER NOT NULL,

                FOREIGN KEY (home_school_id) REFERENCES School (school_id),
                FOREIGN KEY (guest_school_id) REFERENCES School (school_id)
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
                volunteer_code  TEXT     NOT NULL,

                FOREIGN KEY (gala_id) REFERENCES Gala (gala_id)
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
                lane_id         INTEGER NOT NULL,
                event_id        INTEGER NOT NULL,

                heat            INTEGER NOT NULL,
                time            INTEGER NULL,

                PRIMARY KEY (lane_id, event_id),
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

    # Checks if the email exists
    def check_email(self, email):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the user_id of the user with the given email
        c.execute("""
            SELECT user_id
            FROM User
            WHERE email = ?
        """, (email,))

        # Returns true if the user_id is not None
        return c.fetchone() is not None

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
        hash = hash.encode('utf-8')

        # Checks if the password matches the hash
        return bcrypt.checkpw(password, hash)

    # Generates a token so the user can stay logged in
    def generate_token(self, email, expiry):

        # Creates a cursor object to execute SQL commands
        c = self.conn.cursor()

        # Gets the user_id from the email
        c.execute("""
            SELECT user_id
            FROM User
            WHERE email = ?
        """, (email,))
        user_id = c.fetchone()[0]

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
        expiry = c.fetchone()[0]

        # Checks if the token exists
        if expiry is None:
            return False

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

# If database.py is the file being run
if __name__ == '__main__':
	# Creates a database called test.db
	database = Database('test.db')