# coding: utf-8

import json
import sqlalchemy as db

from magneto.libs.store import session, rds
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

    config_key = 'task:%s:config'

    @classmethod
    def create(cls, uuid, seq_id, type, app_id, host_id, cid='', config={}):
        task = cls(uuid=uuid, seq_id=seq_id, type=type,
                app_id=app_id, host_id=host_id, cid=cid)
        try:
            session.add(task)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None
        task.config = config
        return task

    @classmethod
    def get_by_uuid(cls, uuid):
        return session.query(cls).filter(cls.uuid == uuid).\
                order_by(cls.seq_id).all()

    def _get_config(self):
        config = rds.get(self.config_key % self.id)
        return json.loads(config)
    def _set_config(self, config):
        rds.set(self.config_key % self.id, json.dumps(config))
    config = property(_get_config, _set_config)

    def done(self):
        self.status = 1
        session.add(self)
        session.commit()


def task_add_container(app, host):
    from magneto.models.container import get_one_port_from_host
    from magneto.models.user import add_user_for_app

    user = add_user_for_app(app)
    port = get_one_port_from_host(host.id)

    task = {
        'name': app.name.lower(),
        'version': app.version,
        'port': app.port,
        'cmd': app.cmd.split(),
        'host': host.ip,
        'type': 1,
        'uid': user.uid,
        'bind': port,
        'memory': 1024*1024*1024*4,
        'cpus': 100,
        'config': app.config,
    }
    return task


def task_add_containers(app, host):
    from magneto.models.container import get_one_port_from_host
    from magneto.models.user import add_user_for_app

    user = add_user_for_app(app)

    tasks = []
    link = ''
    for cmd in app.cmds:
        port = get_one_port_from_host(host.id)
        task = {
            'name': app.name.lower(),
            'version': app.version,
            'port': app.port,
            'cmd': cmd.split(),
            'host': host.ip,
            'type': 1,
            'uid': user.uid,
            'bind': port,
            'memory': 1024*1024*1024*4,
            'cpus': 100,
            'config': app.config,
            'link': link
        }
        link = '%s_%s' % (app.name, port)
        tasks.append(task)
    return tasks


def task_remove_container(container):
    task = {
        'name': container.app.name.lower(),
        'host': container.host.ip,
        'type': 2,
        'container': container.cid,
    }
    return task


def task_update_container(container, app):
    from magneto.models.container import get_one_port_from_host
    from magneto.models.user import add_user_for_app

    user = add_user_for_app(app)
    port = get_one_port_from_host(container.host.id)

    task = {
        'name': app.name.lower(),
        'uid': user.uid,
        'type': 3,
        'port': app.port,
        'host': container.host.ip,
        'cmd': app.cmd.split(),
        'bind': port,
        'memory': 1024*1024*1024*4,
        'cpus': 100,
        'config': app.config,
        'version': app.version,
        'container': container.cid,
    }
    return task
