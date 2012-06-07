#!/usr/bin/env python2
from __future__ import with_statement
from contextlib import closing
import sqlite3

from flask import Flask, request, session, g, redirect, url_for, \
             abort, render_template, flash

# configuration
DATABASE = '/tmp/wiki.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config(['DATABASE']))

def init_db():
    with closing(connect_db()) as db:
        with app.open_resources('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

if __name__ == '__main__':
    app.run()


