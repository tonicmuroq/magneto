# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base


class Application(Base):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(50), nullable=False)

    @classmethod
    def create(cls, name, version):
        app = cls(name=name, version=version)
        session.add(app)
        session.commit()

    @classmethod
    def get_multi_by_name(cls, name):
        return session.query(cls).filter(cls.name == name).all()

    @classmethod
    def get_by_name_and_version(cls, name, version):
        return session.query(cls).filter(cls.name == name).filter(cls.version == version).one()
