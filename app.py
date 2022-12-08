import functools
import json
from logging import exception
import os
import fileinput
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime
from tkinter import ALL
from django.shortcuts import render

import flask
from flask import render_template, request, Flask, redirect, url_for, flash
from flask import session as login_session
from flask_sqlalchemy import SQLAlchemy


from authlib.client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
from itsdangerous import exc

import google_auth

#Flask app setup and secret key set
app = flask.Flask(__name__)
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)

#SQL database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Setup google auth app
app.register_blueprint(google_auth.app)

ALL_ELPS = []
with open('mentors.EDITME','r+') as fil :
    for line in fil.readlines():
        u,elp = line.split(',')
        elp = elp.strip()
        if elp not in ALL_ELPS:
            ALL_ELPS.append(elp)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=False)

    username = db.Column(db.String(64), unique=True)

    phonenumber = db.Column(db.String(10))

    email = db.Column(db.String(64), unique=True)
    
    ELP = db.Column(db.String(64))

    _password = db.Column(db.String(128))

    def __repr__(self):
        return '<User %r>' % self.username
    def _set_phonenumber(self, plaintext):
        self.phonenumber = plaintext
    def password(self):
        return self._password
    def _set_id(self, plaintext):
        try:
            os.rename(f'Studentlogs/{self.id}.csv',f'Studentlogs/{plaintext}.csv')
        except:
            pass
        self.id = plaintext

    def _set_password(self, plaintext):
        self._password = plaintext

def c_new_user(ID, Uname, Pword, Email, Elp):
    new_u = User(id=ID,username=Uname,_password=str(Pword),email=Email, ELP=Elp)
    db.session.add(new_u)
    flush_db()
    

clockoutlimiter = Limiter(
    app,
    key_func = get_remote_address,
    default_limits=["20/minute","2/second"]
)

db.create_all()


def flush_db():
    try:
        db.session.commit()
    except:
        db.session.rollback()

def is_admin(s):
    admins = ["epicdaface25@gmail.com"]
    with open("admins.EDITME",'r') as a:
        for line in a.readlines():
            admins.append(line.strip())
    print(admins)
    return s in admins
def is_logged_in():
    try:
        return google_auth.is_logged_in() or login_session['logged_in']
    except:
        return False
#LOGIN STUFF

def get_work_boss(email):
    with open('mentors.EDITME','r') as a:
        data = a.readlines()
    k = []
    v = []
    for line in data:
        key,val = line.split(',')
        k.append(key)
        v.append(val)
    d = dict(zip(k,v))
    if email.lower() in k:
        login_session["boss_for"] = d[email].strip()
        print(login_session["boss_for"])
        return True
    return False


@app.route('/')
def index():
    #If google logged in
    if google_auth.is_logged_in():
        uemail = google_auth.get_user_info()['email']
        user_info = google_auth.get_user_info()
        uu = User.query.filter_by(email=uemail).first()
        if get_work_boss(uemail):
            return wbhome()
        if is_admin(uemail):
            login_session['is_admin'] = True
            return render_template("admin_login.html",lou=User.query.filter_by().all(),number=len(os.listdir('./Studentlogs/Submitted')))
        try:
            login_session['ID'] = uu.id
            login_session['phonenumber'] = uu.phonenumber
            login_session['email'] = uemail
        except:
            pass
        try:
            un = User.query.filter_by(email=uemail).first().username
            login_session['username'] = un
            flush_db()
            login_session['logged_in'] = True
            return render_template("logged_in.html", user=un)
        except:
            return "You are not a registered user!!!"
    return render_template("not_logged_in.html")

@app.route('/',methods=['POST'])
def login():
    if is_admin(request.form['email']):
        return render_template("admin_login.html")
    try:
        if request.form['password'] == User.query.filter_by(email=request.form['email']).first()._password:
            login_session['logged_in'] = True
            flush_db()
            a = User.query.filter_by(email=request.form['email']).first().username
            flush_db()
            lia = User.query.filter_by(email=request.form['email']).first()
            flush_db()
            login_session['username'] = a
            login_session['ID'] = lia.id
            login_session['email'] = lia.email
            login_session['password'] = lia._password
            login_session['phonenumber'] = lia.phonenumber
            return render_template("logged_in.html", user=a)
    except:
        pass
    return render_template("not_logged_in.html")+"Incorrect!"


#USER STUFF

@app.route('/settings', methods=["GET","POST"])
def settings():
    if is_logged_in():
        if request.method=='POST':
            u = User.query.filter_by(email=login_session['email']).first()
            num = login_session['phonenumber']

            #Password Validation
            if request.form.get('password') != '':
                if request.form.get('password') == request.form.get('confirm_password'):
                    u._set_password(request.form.get('password'))
                    flush_db()
                else:
                    return render_template("settings.html", number= num)+"<a style='color:red'>Passwords did not match!</a>"
            flush_db()
            return render_template("settings.html"+"<a style='color:green'>Submitted!</a>")
        return render_template("settings.html")
    return redirect('/',302)


#ADMIN STUFF

#New User Creation tab
@app.route('/create_new_user', methods=["GET","POST"])
def create_new_user():
    if is_admin(google_auth.get_user_info()['email']):
        if request.method=='POST':
            c_new_user(request.form.get('ID'),request.form.get('name'), request.form.get('password'),request.form.get('email'),request.form.get('ELP').lower())
            flush_db()
            return "Created!"+"""<a href="/create_new_user"><button>Back</button></a>"""
        return render_template("create_new_user.html", elps=ALL_ELPS)
    else:
        return "You are not an Admin!"

#User deletion!
@app.route('/delete_user/<user>')
def del_user(user):
    if is_admin(google_auth.get_user_info()['email']):
        try:
            todelete = User.query.filter_by(username=user)
            todelete.delete()
            flush_db()
            return "Deleted: "+user+"""\n<a href="/"><button>Back</button></a>"""
        except Exception as e:
            return render_template("delete_user.html")

#ADMIN get report
@app.route('/report/<user>/<id>')
def get_report(user,id):
    if is_admin(google_auth.get_user_info()['email']):
        if login_session['is_admin']:
            with open(f'Studentlogs/{id}.csv','w+') as a:
                cList = a.readlines()
            return render_template('report.html',commentsList=cList,user=user)

#ADMIN edit user
@app.route('/edit/<user>/<cid>', methods=["GET","POST"])
def admin_edit(user,cid):
    print(ALL_ELPS)
    if is_admin(google_auth.get_user_info()['email']):
        uu = User.query.filter_by(id=cid).first()
        print(uu.id)
        if request.method == "GET":
            return render_template('edit_user.html',ID=uu.id,ELP=uu.ELP,Username=uu.username,all_elps=ALL_ELPS)+f"<a href='/delete_user/{uu.username}'><button>Delete</button></a>"
        nid = request.form.get('ID')
        nun = request.form.get('Username')
        npw = request.form.get('Password')
        nel = request.form.get('ELP')
        uu._set_id(nid)
        uu.username = nun
        if nel != "None":
            uu.ELP = nel
        if npw != '':
            uu._set_password(npw)
        flush_db()
        return render_template('edit_user.html',ID=uu.id,ELP=uu.ELP,Username=uu.username,all_elps=ALL_ELPS)+"<a style='color:green'>Submitted!</a><a href='/'><button>Back</button></a>"

@app.route('/clock-out', methods=["GET","POST"])
def clock_out():
    if is_logged_in():
        if request.method == "POST":
            ti = request.form.get("time-in").replace(',',';')
            to = request.form.get("time-out").replace(',',';')
            task = request.form.get("task").replace(',',';')
            careerprep = ["Prep","Non-prep"][None==request.form.get("career-prep")].replace(',',';')
            d = datetime.datetime.now()
            today = d-datetime.timedelta(microseconds=d.microsecond)
            with open('Studentlogs/'+str(login_session['ID'])+'.csv','a+') as doc:
                doc.write(f"{today},{ti},{to},{task},{careerprep}\n")
            return "Success"+"<a href='/'><br><button>Back</button></a>"+"<a style = 'position:fixed;width:100%; right:0px;bottom:0px; text-align: center'>© Trevor Hurst 2022</a><style>    body{background: rgb(0, 0, 0);color: white;}</sytle>"
        return render_template("clock_out.html")


@app.route('/workboss')
def wbhome():
    list_of_users = User.query.filter_by(ELP=login_session['boss_for'])
    add_string = "<div>"
    #Render all the users in the admin screen
    for user in list_of_users:
        add_string+="<ul style='display: inline'>"
        add_string+="<li><label>ID: </label><a>"+str(user.id)+"</a></li>"
        add_string+="<li><label>Username: </label><a>"+user.username+"</a></li>"
        add_string+="<li><label>Email: </label><a>"+user.email+"</a></li>"
        add_string+=f"<a href='/workboss/{user.username}/{str(user.id)}'><button>Get Report</button></a>"
        add_string+=f"<a href='/training_performance/{user.username}/{str(user.id)}'><button>Training Performance</button></a>"
        add_string+="</ul>"
        add_string+="<br>"
    return render_template("workboss_login.html")+add_string

@app.route('/training_performance/<user>/<id>', methods=["GET","POST"])
def tp(user,id):
    if request.method == "GET":
        return render_template("training_performance.html",user=user)
    try:
        os.rename(f'Studentlogs/{id}.csv',f'Studentlogs/Submitted/{id}.csv')
        with open(f'Studentlogs/Submitted/{id}.csv','a+') as a:
            a.write('\n')
            a.write(request.form.get("we_expectations")+',')
            a.write(request.form.get("wc_expectations")+',')
            a.write(request.form.get("we_expectations")+',')
            a.write(request.form.get("a_o_p")+',')
            a.write(request.form.get("a_n_i"))
    except:
        flash("ERROR",category='message')
    return redirect('/workboss',code=302)

@app.route('/EmAiL_SuBmIT')
def email_sub():
    os.system("python emailer.py")
    return redirect('/')


@app.route('/workboss/<user>/<id>', methods=["GET","POST"])
def wb(user,id):
    if request.method == "GET":
        with open(f'Studentlogs/{id}.csv','r') as a:
            data = a.readlines()
        return render_template("workboss.html",commentsList=data)
    out = ''
    for i,j in zip(request.form.values(),range(len(request.form))):
        if j%5==0 and j!=0:
            out+='\n'+str(i).replace(',',';')
            continue
        else:
                out = out+','
        out = out+str(i).replace(',',';')
        with open(f'Studentlogs/{id}.csv','w+') as a:
            a.write(out[1:].strip())
    return "Success"+"<a href='/workboss'><button>Back</button></a>"+"<a style = 'position:fixed;width:100%; right:0px;bottom:0px; text-align: center'>© Trevor Hurst 2022</a>"