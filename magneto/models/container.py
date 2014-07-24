# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base


class Container(Base):
    __tablename__ = 'container'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cid = db.Column(db.String(40), nullable=False)
    host_id = db.Column(db.Integer, nullable=False, index=True)
    app_id = db.Column(db.Integer, nullable=False, index=True)

    @classmethod
    def create(cls, cid, host_id, app_id):
        c = cls(cid=cid, host_id=host_id, app_id=app_id)
        session.add(c)
        session.commit()
