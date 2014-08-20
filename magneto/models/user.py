# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base, IntegrityError


class User(Base):

    __tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    group = db.Column(db.String(50), nullable=False)

    @classmethod
    def create(cls, name, group):
        user = cls(name=name, group=group)
        try:
            session.add(user)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None
        return user

    @classmethod
    def get_by_name(cls, name):
        return session.query(cls).filter(cls.name == name).first()


def add_user_for_app(app):
    name = app.name
    user = User.get_by_name(name)
    if not user:
        user = User.create(name, 'nbe')
    return user
