# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base, IntegrityError


class Host(Base):

    __tablename__ = 'host'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=True, default='')

    @classmethod
    def create(cls, ip, name=''):
        host = cls(ip=ip, name=name)
        try:
            session.add(host)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None
        return host

    @classmethod
    def get_by_ip(cls, ip):
        return session.query(cls).filter(cls.ip == ip).first()
