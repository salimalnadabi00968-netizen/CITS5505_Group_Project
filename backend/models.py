"""
Database models for PerthPins.

Tables:
- User
- CheckIn
- Photo
- Comment
- Favourite
"""

from datetime import datetime, timezone

from flask_login import UserMixin

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Registered PerthPins user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_url = db.Column(db.String(512))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)

    checkins = db.relationship("CheckIn", backref="author", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="author", lazy="dynamic", cascade="all, delete-orphan")
    favourites = db.relationship("Favourite", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class CheckIn(db.Model):
    """Location check-in created by a user."""

    __tablename__ = "check_in"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    place_name = db.Column(db.String(128))
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64), index=True)
    rating = db.Column(db.Float)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)

    photos = db.relationship("Photo", backref="checkin", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="checkin", lazy="dynamic", cascade="all, delete-orphan")
    favourites = db.relationship("Favourite", backref="checkin", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CheckIn {self.title}>"


class Photo(db.Model):
    """Photo attached to a check-in."""

    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    checkin_id = db.Column(db.Integer, db.ForeignKey("check_in.id"), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Photo {self.id} checkin={self.checkin_id}>"


class Comment(db.Model):
    """Comment left on a check-in."""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    checkin_id = db.Column(db.Integer, db.ForeignKey("check_in.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Comment {self.id} by user={self.user_id}>"


class Favourite(db.Model):
    """Saved check-in relationship between a user and a check-in."""

    __tablename__ = "favourites"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    checkin_id = db.Column(db.Integer, db.ForeignKey("check_in.id"), primary_key=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Favourite user={self.user_id} checkin={self.checkin_id}>"
