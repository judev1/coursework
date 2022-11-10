# Imports the Flask object within the flask module
from flask import Flask

# Initiates the Flask object and sets the 'static' folder as the template folder
app = Flask(__name__, template_folder='static')


# Checks to see if the current file is the one being run (ie if another file
# called it then the app should have been run already, this file should on be run
# by itself for debugging)
if __name__ == '__main__':

	# Runs the app with debugging
	app.run(debug=True, use_reloader=False)