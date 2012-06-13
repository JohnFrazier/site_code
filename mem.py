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
        MEMO.app.logger.debug("key: " +  str(key))
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
#@decorator
def page_memo(f):
    def _f(*args, **kwargs):
        MEMO.app.logger.debug(args)
        #MEMO.app.logger.debug(kwargs)
        res=MEMO.get(args)
        #logging.error(args)
        #logging.error(MEMO.cache.keys())
        #logging.error(MEMO.cache.values())
        if res:
            #logging.error("cache hit")
            #MEMO.app.logger.debug(type(res))
            #res, qtime = res
            #res[1]['rtime']=time
            #logging.error(res)
            #MEMO.app.logger.debug(res)
            return res
        else:
            #logging.error("cache miss")
            res = f(*args) # page_name=page_name)
            MEMO.set(args, (res, time.time()))
            res, qtime = MEMO.get(args)
            if res:
                #res, time = res
                #res[1]["rtime"]=time
                return res, qtime
            return False
    return _f
