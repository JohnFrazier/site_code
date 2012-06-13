#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import closing
import re
import sqlite3
import codecs
import json
import time
from docutils.core import publish_parts, publish_string

from flask import Flask, Response, request, session, g, redirect, url_for, \
             abort, render_template, flash
from flask.views import MethodView

import passw
import mem
# configuration
DATABASE = '/tmp/wiki.db'
DEBUG = True
import secret
SECRET_KEY = secret.KEY

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

def get_response_type(accept_string):
    for s, v in accept_string:
        if s == 'application/json' and v > .9:
            return 'json'
        if s == 'text/text' and v > .9:
            return 'text'
        return 'html'

class Index(MethodView):
    def get(self):
        return redirect("/Page_Index")

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
            user = g.db.execute("SELECT password,salt from User WHERE username=?",
                                (name,)).fetchone()
        if user:
            if passw.valid_pw(name, pw, user[0], user[1]):
                flash("Welcome back %s!" % name)
                session['username'] = name
                return redirect(url_for('index'))
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
            salt = passw.make_salt()
            password = passw.make_pw_hash(name, pw, salt)
            g.db.execute(
                "insert into user (username, salt, ctime, password) values (? ,?, ?, ?)",
                         [name, salt, time.time(), password])
            flash("Welcome %s!" % name)
            g.db.commit()
            return redirect(url_for('index'))

class Logout(MethodView):
    def get(self):
        session.pop('username', None)
        flash("Sucessfully logged out")
        #self.response.headers.add_header('Set-Cookie', 'name=; Path=/')
        return redirect(url_for('index'))
mem.MEMO.app = app

@mem.page_memo
def page_render_content(page_name, response_type):
    #app.logger.debug(response_type)
    f=None
    fname='pages/' + page_name + ".txt"
    content = u""
    # so docutils will output a unicode string
    overrides= {'input_encoding': 'unicode', 'output_encoding': 'unicode'}
    try:
        with codecs.open(fname, encoding='utf-8') as f:
            s=f.read()#.decode('utf-8')
            if response_type == 'html':
                # I need docutils to dump just the body not head and style
                return publish_parts(source=s, #.read().encode('utf-8'),
                                       settings_overrides=overrides,
                                       writer_name='html')['html_body']
            elif response_type == 'json':
                d={'*': s, 'query': page_name}
                content = json.dumps(d)
                mime='Application/json'
                return Response(content, mimetype=mime)
            elif response_type == 'text':
                return Response(s, mimetype='text/text')
            else: return "failed"
    except IOError: flash("something went wrong, page not found")

class Page(MethodView):
    def get(self, page_name=""):
        response_type=get_response_type(request.accept_mimetypes)
        content, qtime= page_render_content(page_name, response_type)
        rtime = int(time.time() - qtime) 
        if response_type == "html":
            return render_template("page.html", nav=get_nav(), rtime=rtime,
                               page_content=content, page_name=page_name)
        return content

def get_nav(path=None):
    result={}
    result['main'] = ("home", url_for('index'))
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
        result["user"]=(session['username'], "") #url_for('index'))
        result["logout"]=("logout", url_for('logout'))
    else:
        result["user"]=("Not logged in", url_for("login"))
        result["login"]=( "login", url_for("login"))
        result['signup']=("sign up", url_for("signup"))

    # create a nav dict
    return result

PAGE_RE = r'/([a-zA-Z0-9_-]+)/?'
if __name__ == '__main__':
    app.add_url_rule('/logout', view_func=Logout.as_view('logout'))
    app.add_url_rule('/login', view_func=Login.as_view('login'))
    app.add_url_rule('/signup', view_func=Signup.as_view('signup'))
    app.add_url_rule('/', view_func=Index.as_view('index'))
    app.add_url_rule('/<page_name>', view_func=Page.as_view('page'))
    app.run()


