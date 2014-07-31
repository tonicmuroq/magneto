# coding: utf-8

import json
import sqlalchemy as db
from random import sample

from magneto.libs.store import session, rds
from magneto.models import Base, IntegrityError


DEFAULT_PORT_RANGE = (49000, 50000)
_HOST_PORTS_LOCK = 'host:ports:lock:%s'
_HOST_PORTS_KEY = 'host:ports:%s'


class Container(Base):

    __tablename__ = 'container'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cid = db.Column(db.String(40), nullable=False)
    host_id = db.Column(db.Integer, nullable=False, index=True)
    app_id = db.Column(db.Integer, nullable=False, index=True)
    status = db.Column(db.Integer, nullable=False, default=0)
    port = db.Column(db.Integer, nullable=False, default=0)

    status_key = 'container:%s:status'

    @classmethod
    def create(cls, cid, host_id, app_id, port=0):
        c = cls(cid=cid, host_id=host_id, app_id=app_id, port=port)
        try:
            session.add(c)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None
        return c

    @classmethod
    def get_by_cid(cls, cid):
        return session.query(cls).filter(cls.cid == cid).first()

    @classmethod
    def get_multi_by_host(cls, host_id):
        return session.query(cls).filter(cls.host_id == host_id).all()

    @classmethod
    def get_multi_by_host_and_app(cls, host_id, app_id):
        return session.query(cls).filter(cls.host_id == host_id).\
                filter(cls.app_id == app_id).all()

    def _get_status(self):
        status = rds.get(self.status_key % self.id)
        return json.loads(status)
    def _set_status(self, status):
        rds.set(self.status_key % self.id, json.dumps(status))
    status = property(_get_status, _set_status)

    def delete(self):
        session.delete(self)
        session.commit()
        remove_ports_from_host(self.host_id, [self.port])

    @property
    def app(self):
        from magneto.models.application import Application
        return Application.get(self.app_id)

    @property
    def host(self):
        from magneto.models.host import Host
        return Host.get(self.host_id)


def dispatch_ports_on_host(host_id, count, port_range=DEFAULT_PORT_RANGE):
    with rds.lock(_HOST_PORTS_LOCK % host_id, timeout=10, sleep=2):
        aps = set([i for i in xrange(*DEFAULT_PORT_RANGE)])
        cps = rds.smembers(_HOST_PORTS_KEY % host_id)
        rs = sample(aps - cps, count)
        rds.sadd(_HOST_PORTS_KEY % host_id, *rs)
        return rs


def remove_ports_from_host(host_id, ports=[]):
    with rds.lock(_HOST_PORTS_LOCK % host_id, timeout=10, sleep=2):
        rds.srem(_HOST_PORTS_KEY % host_id, *ports)


def get_one_port_from_host(host_id, port_range=DEFAULT_PORT_RANGE):
    rs = dispatch_ports_on_host(host_id, count=1, port_range=port_range)
    return rs[0]
