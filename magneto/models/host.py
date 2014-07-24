# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base


class Host(Base):
    __tablename__ = 'host'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=True, default='')

    @classmethod
    def create(cls, ip, name=''):
        host = cls(ip=ip, name=name)
        session.add(host)
        session.commit()
