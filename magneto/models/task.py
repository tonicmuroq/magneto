# coding: utf-8

import sqlalchemy as db

from magneto.libs.store import session
from magneto.models import Base


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
        session.add(task)
        session.commit()

    @classmethod
    def update_multi_status(cls, uuid, status_list):
        tasks = session.query(cls).filter(cls.uuid == uuid).\
                order_by(cls.seq_id).all()
        # TODO: error
        if len(tasks) != len(status_list):
            return
        # 一次提交
        for task, status in zip(tasks, status_list):
            task.status = status
        session.commit()

    @classmethod
    def get_by_uuid(cls, uuid):
        return session.query(cls).filter(cls.uuid == uuid).\
                order_by(cls.seq_id).all()

    def done(self):
        self.status = 1
        session.add(self)
        session.commit()
