import memcache
import time
from functools import update_wrapper

def decorator(d):
    "Make function d a decorator: d wraps a function fn."
    def _d(fn, app):
        return update_wrapper(d(fn), fn)
    update_wrapper(_d, d)
    return _d
import hashlib

class Memo():
    def get_key(self,x):
        return ''.join((s for s in x)).encode('latin')
        #hashlib.sha1(x).digest()
    def __init__(self):
        self.cache=memcache.Client(['127.0.0.1:11211'], debug=0)
    def get(self, key):
        #MEMO.app.logger.debug("key: " +  str(key))
        k=self.get_key(key)
        try:
            return self.cache.get(k)
        except KeyError:
            return None

    def gets(self,key):
        k=self.get_key(key)
        val, time=self.get(k)
        if val:
            return val, hash(repr(val))
        return None

    def set(self, key, value):
        k=self.get_key(key)
        try:
            self.cache.set(k, value) #, time.time()))
        except TypeError:
            return False
        return True

    def cas(self, key, value, hash):
        # fancy sety
        k=self.get_key(key)
        r,t = gets(key)
        if r:
            if hash == r[1]:
                return self.set(k , value)
            else:
                return False
    def delete(self, key):
        k=self.get_key(key)
        self.cache.delete(k)

    def flush(self):
        self.cache.flush_all()
MEMO= Memo()
MEMO.flush()

def page_memo(f):
    def _f(*args, **kwargs):
        res=MEMO.get(args)
        if res:
            #MEMO.app.logger.debug("cache hit")
            return res
        else:
            #MEMO.app.logger.debug("cache miss")
            res = f(*args) # page_name=page_name)
            MEMO.set(args, (res, time.time()))
            if res:
                return res, time.time()
            return False, 0
    return _f
