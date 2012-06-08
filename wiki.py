#!/usr/bin/env python2
from __future__ import with_statement
from contextlib import closing
import re
import sqlite3

from flask import Flask, request, session, g, redirect, url_for, \
             abort, render_template, flash

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
                               escape(session['username']))
        else:
            return render_template("welcome.html", 
                               welcome_msg="You are not welcome stranger")


class Login(MethodView):
    def get(self, username=None):
        if username:
            return render_template("login.html", username=username)
        else:
            return render_template("login.html")

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
            return redirect("/welcome")
        else:
            flash("Invalid User and/or Password")
            return self.get(username = name)


if __name__ == '__main__':
    init_db()
    app.add_url_rule('/login', view_func=Login.as_view('login'))
    app.add_url_rule('/', view_func=Index.as_view('index'))
    app.run()


