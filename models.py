import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    downloads = db.relationship('Download', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_download_count(self):
        return self.downloads.count()


class Download(db.Model):
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(500))
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'youtube_url': self.youtube_url,
            'filename': self.filename,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }


class History(db.Model):
    __tablename__ = 'history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    video_id = db.Column(db.String(50))
    playlist_id = db.Column(db.String(100))
    thumbnail = db.Column(db.String(500))
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('history_items', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'youtube_url': self.youtube_url,
            'video_id': self.video_id,
            'playlist_id': self.playlist_id,
            'thumbnail': self.thumbnail,
            'played_at': self.played_at.isoformat() if self.played_at else None
        }


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    video_id = db.Column(db.String(50))
    playlist_id = db.Column(db.String(100))
    thumbnail = db.Column(db.String(500))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('favorites', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'youtube_url': self.youtube_url,
            'video_id': self.video_id,
            'playlist_id': self.playlist_id,
            'thumbnail': self.thumbnail,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }


class Playlist(db.Model):
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    video_id = db.Column(db.String(50))
    playlist_id = db.Column(db.String(100))
    thumbnail = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('playlists', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'youtube_url': self.youtube_url,
            'video_id': self.video_id,
            'playlist_id': self.playlist_id,
            'thumbnail': self.thumbnail,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
