import bcrypt 

def make_salt():
    return bcrypt.gensalt()

def make_pw_hash(name, pw, salt):
    try:
        h = bcrypt.hashpw(name + pw, salt)
    except ValueError:
        h=None
    return h

def valid_pw(name, pw, h, salt):
    return h == make_pw_hash(name, pw, salt)
