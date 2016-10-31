from google.appengine.ext import db
import jinja2
from handler import *




class Post(db.Model):
    """Post is the Object Model for the Blog Post."""
    """The attributes include the subject and content of the blog post"""
    """Also includes the date the object was created and last modified"""
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    author = db.StringProperty(required = True)
    user_id=db.IntegerProperty(required = True)
    liked_by_list = db.ListProperty(str)
    likes = db.IntegerProperty(required=True)
    dislikes = db.IntegerProperty(required = True)


    def render(self):
        """The render function renders it into HTML and shows multiline in HTML"""
        self._render_text = self.content.replace('\n', '<br/>')
        return render_str("post.html", p = self)

    def username(self):
        """retrieves the username"""
        user = User.by_name(self.user_id)
        return user.name


class Comment(db.Model):
    """The Comment Model handles and stores the comments from blog users"""
    comment = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    created_by = db.StringProperty(required = True)
    post_id = db.IntegerProperty(required = True)

    def formatted_comment(self):
        if not self.comment:
            return ""
        else:
            return self.comment.replace('\n', '<br/>')
