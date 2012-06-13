#import random
#import string
#import hashlib
import bcrypt 

def make_salt():
    return bcrypt.gensalt()
#return ''.join(random.sample(string.letters, 5))

def make_pw_hash(name, pw, salt=None):
    if salt == None:
        salt=make_salt()
    #h = hashlib.sha256(name + pw + salt).hexdigest()
    try:
        h = bcrypt.hashpw(name + pw, salt)
    except ValueError: return None, None
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    n,salt = h.split(',')
    return h == make_pw_hash(name, pw, salt)
