#-*- encoding: utf-8 -*-
"""
models.py

"""
from apps import db
from datetime import datetime
from flask.ext.login import UserMixin


class Tag(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    article_count = db.Column(db.Integer, default=0)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255))
    content = db.Column(db.Text())

    like_count = db.Column(db.Integer)
    like_history = db.Column(db.Text())
    like_history_user = db.Column(db.Text())

    user_id = db.Column(db.String(255), db.ForeignKey('user.id'))
    user = db.relationship('User', 
        foreign_keys=[user_id],
        primaryjoin="Article.user_id==User.id",
        backref=db.backref('articles', cascade='all, delete-orphan'))

    tag_id = db.Column(db.String(255), db.ForeignKey('tag.id'))
    tag = db.relationship('Tag',
        foreign_keys=[tag_id],
        primaryjoin="Article.tag_id==Tag.id",
        #backref=db.backref('articles', cascade='all, delete-orphan', lazy='dynamic'))
        backref=db.backref('articles', cascade='all, delete-orphan'))

    comment_count = db.Column(db.Integer, default=0)

    date_created = db.Column(db.DateTime(), default=db.func.now())

    files = db.Column(db.String(255), default="")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    article = db.relationship('Article',
        foreign_keys=[article_id],
        primaryjoin="Comment.article_id==Article.id",
        backref=db.backref('comments', cascade='all, delete-orphan'))

    # 유저 아이디 입력 받은걸로 get해서 객체를 user 에 저장
    user_id = db.Column(db.String(255), db.ForeignKey('user.id'))
    user = db.relationship('User', 
        foreign_keys=[user_id],
        primaryjoin="Comment.user_id==User.id",
        backref=db.backref('comments', cascade='all, delete-orphan'))

    content = db.Column(db.Text())

    date_created = db.Column(db.DateTime(), default=db.func.now())


class User(UserMixin, db.Model):
    id = db.Column(db.String(255), primary_key=True) # 중복 확인 
    pw = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(64), default="")
    photo = db.Column(db.String(255), default="") # file name (picture)
    date_joined = db.Column(db.DateTime, default=db.func.now())
    
    def __repr__(self):
        return '<User %r>' % (self.name)
