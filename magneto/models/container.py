# coding: utf-8

import json
import sqlalchemy as db

from magneto.libs.store import session, rds
from magneto.models import Base


class Container(Base):
    __tablename__ = 'container'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cid = db.Column(db.String(40), nullable=False)
    host_id = db.Column(db.Integer, nullable=False, index=True)
    app_id = db.Column(db.Integer, nullable=False, index=True)

    __status_key__ = 'container:%s:status'

    @classmethod
    def create(cls, cid, host_id, app_id):
        c = cls(cid=cid, host_id=host_id, app_id=app_id)
        session.add(c)
        session.commit()

    @classmethod
    def get_by_cid(cls, cid):
        session.query(cls).filter(cls.cid == cid).one()

    def _get_status(self):
        status = rds.get(self.__status_key__ % self.id)
        return json.loads(status)

    def _set_status(self, status):
        rds.set(self.__status_key__ % self.id, json.dumps(status))

    status = property(_get_status, _set_status)
