import functools
import json
import os
import fileinput

import flask
from flask import render_template, request

from authlib.client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery

import google_auth

app = flask.Flask(__name__)
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)

app.register_blueprint(google_auth.app)

@app.route('/')

def index():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        return render_template("logged_in.html", user=user_info['given_name'])

    return render_template("not_logged_in.html")

@app.route('/settings')
def settings():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        return render_template("settings.html", number= user_info['given_name'])

@app.route('/settings',methods=['POST'])
def settings_post():
    print(request.form['phone_number'])
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        for line in fileinput.input(["phone#s.txt"],inplace=True):
            print("LINE:",line)
        return render_template("settings.html", number= user_info['given_name'])
    return render_template("not_logged_in.html")
