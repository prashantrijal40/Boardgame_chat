from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

# Association table for hidden links
hidden_links = db.Table('hidden_links',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('link_id', db.Integer, db.ForeignKey('link.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    boardgame_points = db.Column(db.Integer, default=0)

    links = db.relationship('Link', backref='author', lazy=True)
    ratings = db.relationship('Rating', backref='rater', lazy=True)

    # New: hidden links relationship
    hidden = db.relationship('Link',
                             secondary=hidden_links,
                             backref='hidden_by',
                             lazy='dynamic')

    def __repr__(self):
        return f"<User {self.username}, Points: {self.boardgame_points}>"

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ratings = db.relationship('Rating', backref='link', lazy=True)

    def aggregate_rating(self):
        return sum(r.value for r in self.ratings)

    def __repr__(self):
        return f"<Link {self.title} by User {self.user_id}>"

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)  # 1 for upvote, -1 for downvote

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=False)

    def __repr__(self):
        return f"<Rating {self.value} by User {self.user_id} for Link {self.link_id}>"
