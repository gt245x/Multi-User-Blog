import os
import jinja2
import webapp2
import re
from string import letters

from handler import *
from Model import *


template_dir = os.path.join(os.path.dirname(__file__),'templates').replace("\\","/")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)




class MainPage(BlogHandler):
    """self.writes to the mainpage"""
    def get(self):
        self.write("Welcome to Project multi user blog")

class Signup(BlogHandler):
    """Renders and handles signup for the blog page"""
    def get(self):
        self.render("signup-form.html")

    def post(self):
        """retrieves the username, password, email from the signup-form"""
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify_password')
        self.email = self.request.get('email')

        params = dict(username = self.username, email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True

        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()
    def done(self):
        u = User.by_name(self.username)
        if u:
            msg = 'That username already exists.'
            self.render('signup-form.html', username = self.username, error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
            self.login_set_cookie(u)
            self.redirect('/blog')

class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')



class BlogFront(BlogHandler):
    """Renders the blog page with the top 10 posts"""
    def get(self):
        posts = Post.all().order('-created')
        self.render('front.html', posts = posts)



class PostPage(BlogHandler):
    """Renders and handles a single blog including comments for that single blog"""
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)

        comments = Comment.all().filter('post_id =', int(post_id)).order('-created')
        # comments = db.GqlQuery("SELECT * FROM Comment where post_id = " + post_id + " ORDER BY created DESC")

        if not post:
            self.error(404)
            return
        self.render("permalink.html", post = post, comments = comments)




class NewPost(BlogHandler):
    """Renders and handles new blog posts for the blog"""
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect('/login')

    def post(self):
        if not self.user:
            self.redirect('/blog')

        subject = self.request.get("subject")
        content = self.request.get("content")
        author = self.request.get("author")

        if subject and content:
            p = Post(parent = blog_key(),
                     subject = subject,
                     content = content,
                     author = author,
                     user_id = self.user.key().id(),
                     likes=0,
                     dislikes=0,
                     liked_by_list=[])


            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!!!!!"
            self.render("newpost.html", subject = subject, content = content, error = error)

class Login(BlogHandler):
    """Renders and handles login for the blog page"""
    def get(self):
        self.render('login-form.html')

    def post(self):
        self.username = self.request.get('username')
        self.password = self.request.get('password')

        u = User.login(self.username, self.password)
        if u:
            self.login_set_cookie(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', username = self.username, error = msg)

class Logout(BlogHandler):
    """Renders and handles logout for the blog page"""
    def get(self):
        self.logout_cookie()
        self.redirect('/blog')


class EditPost(BlogHandler):
    """Renders and handles editing for each blog post"""
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        if self.user:
            if self.user.name == post.author:
                self.render('editpost.html',
                            subject = post.subject,
                            content = post.content,
                            post_id = post_id,
                            )
            else:
                message = ("You can only edit a post created by you")
                self.render('confirm.html', message = message)
        else:
            self.redirect('/login')


    def post(self, post_id):
        if not self.user:
            self.redirect ('/login')
        else:
            key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(key)
            if post:
                if self.user.name == post.author:
                    subject = self.request.get("subject")
                    content = self.request.get("content")

                    if subject and content:
                        post.subject = subject
                        post.content = content
                        post.put()
                        self.redirect('/blog/%s' % str(post.key().id()))


                    else:
                        message = "subject and content, please!!!!!"
                        self.render('editpost.html', subject = subject, content = content, error = message)
                else:
                    message = "Only the author can edit the post"
                    self.render('confirm.html', message = message)
            else:
                self.error(404)
                return




class DeletePost(BlogHandler):
    """Renders and handles deleting of each post"""
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        if self.user:
            if self.user.name == post.author:
                post.delete()
                message = "The selected post was successfully deleted"
                self.render('confirm.html', message = message)
            else:
                message = "You don't have permission to delete this post."
                self.render('confirm.html', message = message)
        else:
            self.redirect('/login')




class CommentPost(BlogHandler):
    """Renders and handles new commenting for each post"""
    def get(self, post_id):
        if self.user:
            self.render("commentpost.html", post_id = post_id)
        else:
            redirect('/login')

    def post(self, post_id):
        if self.user:
            comment_str = self.request.get("comment")
            created_by = self.request.get("created_by")
            key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(key)

            if not post:
                self.error(404)
                return

            if comment_str:
                c = Comment(parent = blog_key(),
                            comment =comment_str,
                            created_by = created_by,
                            post_id = int(post_id))
                c.put()
                self.redirect('/blog/%s' % post.key().id())
            else:
                error = "Please add some comment"
                self.render("commentpost.html", error = error)
        else:
            self.redirect('login')

class Deletecomment(BlogHandler):
    """Renders and handles deleting of each comment"""
    def get(self,comment_id):
        if self.user:
            key = db.Key.from_path('Comment', int(comment_id), parent = blog_key())
            comment = db.get(key)
            if not comment:
                self.error(404)
                return
            if self.user.name == comment.created_by:
                comment.delete()
                message = "The selected comment was successfully deleted"
                self.render('confirm.html', message = message)
            else:
                message = "You don't have permission to delete this comment."
                self.render('confirm.html', message = message)
        else:
            self.redirect('/login')

class Editcomment(BlogHandler):
    """Renders and handles editing og each comment"""
    def get(self, post_id, comment_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
        comment_key = db.Key.from_path('Comment', int(comment_id), parent = blog_key())
        comment = db.get(comment_key)
        if not post and comment:
            self.error(404)
            return
        if self.user:
            if self.user.name == comment.created_by:
                self.render('editcomment.html', comment = comment.comment)
            else:
                msg = "You can only edit a comment that you created."
                self.render('confirm.html', message = msg)

        else:
            self.redirect('/login')


    def post(self, post_id, comment_id):
        if not self.user:
            self.redirect('/login')
        else:
            key = db.Key.from_path('Post', int(comment_id), parent = blog_key())
            post = db.get(key)
            comment_key = db.Key.from_path('Comment', int(comment_id), parent = blog_key())
            comment = db.get(comment_key)
            if comment:
                if self.user.name == comment.created_by:
                    comment_str = self.request.get('comment')
                    if comment_str:
                        comment.comment = comment_str
                        comment.put()
                        self.redirect('/blog/%s' % str(post_id))
                    else:
                        message = "Make sure your comments are added before submitting!!!"
                        self.render('editcomment.html', error = message)
                else:
                    message = "You can only edit comments that you created"
                    self.render('editcomment.html', comment = comment, error = message)
            else:
                self.error(404)
                return



class LikePost(BlogHandler):
    """Handles how many likes each post gets"""
    def get(self, post_id):
        if not self.user:
            self.redirect('/login')
        else:
            post_key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(post_key)
            current_user = self.user.name
            post_author = post.author

            if post:
                if post_author != current_user and current_user not in post.liked_by_list:
                    post.likes +=1
                    post.liked_by_list.append(current_user)
                    post.put()
                    self.redirect('/blog')
                else:
                    message = "You cannot like the blog post more than once or like the post if you are the author"
                    self.render('confirm.html', message = message)
            else:
                self.error(404)
                return





class DisLikePost(BlogHandler):
    """Handles how many dislike each post gets"""
    def get(self, post_id):
        if not self.user:
            self.redirect('/login')
        else:
            post_key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(post_key)
            current_user = self.user.name
            post_author = post.author

            if post:
                if post_author != current_user and current_user not in post.liked_by_list:
                    post.dislikes +=1
                    post.liked_by_list.append(current_user)
                    post.put()
                    self.redirect('/blog')
                else:
                    message = "You cannot dislike the blog post more than once or dislike the post if you are the author"
                    self.render('confirm.html', message = message)
            else:
                self.error(404)
                return






app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', Signup),
    ('/welcome', Welcome),
    ('/blog/?', BlogFront),
    ('/blog/([0-9]+)', PostPage),
    ('/blog/newpost', NewPost),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog/delete/([0-9]+)', DeletePost),
    ('/blog/editpost/([0-9]+)', EditPost),
    ('/blog/comment/([0-9]+)', CommentPost),
    ('/blog/deletecomment/([0-9]+)', Deletecomment),
    ('/blog/editcomment/([0-9]+)/([0-9]+)', Editcomment),
    ('/blog/likepost/([0-9]+)', LikePost),
    ('/blog/dislikepost/([0-9]+)', DisLikePost)
], debug=True)


