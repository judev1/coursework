import sqlite3
import os


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


# If database.py is the file being run
if __name__ == '__main__':
	# Creates a database called test.db
	database = Database('test.db')
