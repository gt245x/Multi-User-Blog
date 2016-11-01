import re
import os
import jinja2
import webapp2
import hashlib
from string import letters
import random
import hmac

from google.appengine.ext import db



template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))


secret = 'good'

def make_secure_val(val):
    """takes a string and returns a string of the format s, HASH"""
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    """takes a string of the format s|HASH and returns s if hash_str(s) == HASH"""
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

def make_salt(length = 5):
    """returns a string of 5 random letters using random module"""
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    """returns a hashed password of the format HASH(name + pw + salt), salt using sha256"""
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s, %s' % (salt, h)

def valid_pw(name, password, h):
    """returns true if a user's password matches its hash"""
    salt = h.split(',')[0]
    return h ==make_pw_hash(name, password, salt)


def users_key(group = 'default'):
    """parent key for storing users"""
    return db.Key.from_path('users', group)

def blog_key(name = 'default'):
    """parent key for blog database"""
    return db.Key.from_path('blogs', name)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    """the 3 templates handles self.write with extra parameters"""
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params["user"] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        """sets the cookie header and the path"""
        cookie_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s; Path=/'
                                         % (name, cookie_val))

    def read_secure_cookie(self, name):
        """confirms that the cookie is authentic and has not been tampered with"""
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login_set_cookie(self, user):
        """Sets cookie for each user that logs in"""
        self.set_secure_cookie('user_id', str(user.key().id()))

    def initialize(self, *a, **kw):
        """initialies each user by confirming their cookie"""
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

    def logout_cookie(self):
        """logs out the user by setting their cookie to empty"""
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty

    @classmethod
    def by_id(cls, uid):
        return cls.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return cls(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u




######



