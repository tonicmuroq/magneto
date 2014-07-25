# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base, IntegrityError


class Task(Base):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(50), nullable=False, index=True)
    seq_id = db.Column(db.Integer)
    type = db.Column(db.Integer)
    status = db.Column(db.Integer, nullable=False, default=0)
    app_id = db.Column(db.Integer, nullable=False)
    host_id = db.Column(db.Integer, nullable=False)
    cid = db.Column(db.String(50), nullable=False, default='')

    @classmethod
    def create(cls, uuid, seq_id, type, app_id, host_id, cid=''):
        task = cls(uuid=uuid, seq_id=seq_id, type=type,
                app_id=app_id, host_id=host_id, cid=cid)
        try:
            session.add(task)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None
        return task

    @classmethod
    def get_by_uuid(cls, uuid):
        return session.query(cls).filter(cls.uuid == uuid).\
                order_by(cls.seq_id).all()

    def done(self):
        self.status = 1
        session.add(self)
        session.commit()
