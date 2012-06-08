#!/usr/bin/env python2
from __future__ import with_statement
from contextlib import closing
import re
import sqlite3

from flask import Flask, request, session, g, redirect, url_for, \
             abort, render_template, flash

import passw, time
# configuration
DATABASE = '/tmp/wiki.db'
DEBUG = True
SECRET_KEY = 'K\xa3z\xc3\x92\x03-\xecns\xb9q\xd1\x99\xb4\xb0\x8c,\xd7\x8b\x82\xff\xe3\xfb'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

from flask.views import MethodView

class Index(MethodView):
    def get(self):
        if 'username' in session:
            return render_template("welcome.html", welcome_msg="welcome %s" %
                               session['username'][1], nav=get_nav())
        else:
            return render_template("welcome.html", nav=get_nav(), 
                               welcome_msg="You are not welcome stranger")

class Login(MethodView):
    def get(self, username=None):
        if username:
            return render_template("login.html", username=username,
                                   nav=get_nav())
        else:
            return render_template("login.html", nav=get_nav())

    def post(self):
        name = request.form['username']
        pw = request.form['password']
        user=None
        if re.compile("^[a-zA-Z0-9_-]{3,20}$").match(name):
            user = g.db.execute("SELECT * from User WHERE username=?",
                                (name,)).fetchone()
            app.logger.debug("foo")
        if user:
            session['username'] = user
            return redirect(url_for('index'))
        else:
            flash("Invalid User and/or Password")
            return self.get(username = name)

class Signup(MethodView):
    def get(self, username=None):
        if username:
            return render_template("signup.html", username=username,
                                   nav=get_nav())
        else:
            return render_template("signup.html", nav=get_nav())
    def post(self):
        requests={"username": {"pat": re.compile("^[a-zA-Z0-9_-]{3,20}$"), 
                               "err": "That's not a valid username."},
                  "email": {"pat": re.compile("^[\S]+@[\S]+\.[\S]+$"), 
                            "err": "That's not a valid email."},
                  "password": {"pat": re.compile("^.{3,20}$"), 
                               "err": "Invalid Password"},
                  "verify": {"pat": re.compile(".*") , "err": "Your passwords didn't match."}}
        p={"username": "", "email": ""}
        responses=dict((key, request.form[key]) for key in requests)
        errors=False
        
        for k,v in requests.iteritems():
            if not responses[k] or not v['pat'].match(responses[k]):
                if k == 'email' and responses[k] == "":
                    pass
                else:
                    flash(v["err"])
                    errors=True
                    break
       
        if not errors and  responses['password'] and responses['verify']:
            if responses['password'] != responses['verify']:
                errors=True
                flash(requests['verify']["err"])
        
        pw=responses['password']
        name=responses['username']

        if g.db.execute("select * from User WHERE username=?",
                           (name,)).fetchone():
            errors = True
            flash( "Username is taken")
        
        if errors:
            p["username"] = name
            p["email"] = responses['email']
            return render_template("signup.html", username=name)
        
        else:
            session['username'] = name
            #cname=cookies.make_secure_val(name)
            #self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' %
            #                                 cname )
            g.db.execute(
                "insert into user (username, ctime, password) values (?, ?, ?)",
                         [name, time.time(), passw.make_pw_hash(name, pw)])
            g.db.commit()
            return redirect(url_for('index'))

class Logout(MethodView):
    def get(self):
        session.pop('username', None)

        #self.response.headers.add_header('Set-Cookie', 'name=; Path=/')
        return redirect(url_for('index'))

def get_nav(path=None):
        result={}
        # check user logins add user info to the result
        if path:
            result['edit']=("edit page", "/_edit/" + path)
            result["history"]=("page history", "/_history/" + path)
            result["latest"]=("latest version", path)
            #result["page_name"] = path 
        else:
            pass
            #page=self.request.path 
            #result['page_name']= page
        if 'username' in session:
            result["user"]=(session['username'][1], '/')
            result["logout"]=("logout", url_for('logout'))
        else:
            result["user"]=("Not logged in", url_for("login"))
            result["login"]=( "login", url_for("login"))
            result['signup']=("sign up", url_for("signup"))

        # create a nav dict
        return result
if __name__ == '__main__':
    app.add_url_rule('/logout', view_func=Logout.as_view('logout'))
    app.add_url_rule('/login', view_func=Login.as_view('login'))
    app.add_url_rule('/signup', view_func=Signup.as_view('signup'))
    app.add_url_rule('/', view_func=Index.as_view('index'))
    app.run()


