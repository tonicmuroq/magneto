# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base, IntegrityError, OperationalError


class Host(Base):

    __tablename__ = 'host'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=True, default='')
    status = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def create(cls, ip, name=''):
        host = cls(ip=ip, name=name)
        try:
            session.add(host)
            session.commit()
        except (IntegrityError, OperationalError):
            session.rollback()
            return None
        return host

    @classmethod
    def get_by_ip(cls, ip):
        return session.query(cls).filter(cls.ip == ip).first()

    @classmethod
    def get(cls, id):
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_multi_by_ip(cls, ips):
        return [cls.get_by_ip(ip) for ip in ips]

    @classmethod
    def register(cls, ip, name=''):
        host = cls.get_by_ip(ip)
        if host and host.is_offline():
            host.online()
            return host
        host = cls.create(ip, name)

    def online(self):
        self.status = 0
        session.add(self)
        session.commit()

    def offline(self):
        self.status = 1
        session.add(self)
        session.commit()

    def is_online(self):
        return self.status == 0

    def is_offline(self):
        return self.status == 1
