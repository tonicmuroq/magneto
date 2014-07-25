# coding: utf-8

import json
import sqlalchemy as db

from magneto.libs.store import session, rds
from magneto.models import Base, IntegrityError


def get_service_config(service):
    '''just example'''
    if service == 'redis':
        return {
            'host': '192.168.1.120',
            'port': 6379,
        }
    if service == 'mysql':
        return {
            'host': '192.168.1.153',
            'port': 3306,
            'username': 'root',
            'password': '',
        }
    return {}


class Application(Base):

    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(50), nullable=False)

    app_yaml_key = 'app:app_yaml:%s'
    config_yaml_key = 'app:config_yaml:%s'
    gen_config_yaml_key = 'app:gen_config_yaml:%s'

    @classmethod
    def create(cls, name, version, app_yaml=None, config_yaml=None):
        if not app_yaml:
            return None
        if not config_yaml:
            config_yaml = '{}'

        app = cls(name=name, version=version)
        try:
            session.add(app)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None

        rds.set(app.app_yaml_key % app.id, app_yaml)
        rds.set(app.config_yaml_key % app.id, config_yaml)
        app.gen_config_yaml()
        return app

    @classmethod
    def get_multi_by_name(cls, name):
        return session.query(cls).filter(cls.name == name).all()

    @classmethod
    def get_by_name_and_version(cls, name, version):
        return session.query(cls).filter(cls.name == name).\
                filter(cls.version == version).one()

    @property
    def app_yaml(self):
        return json.loads(rds.get(self.app_yaml_key % self.id))

    @property
    def config_yaml(self):
        return json.loads(rds.get(self.config_yaml_key % self.id))

    @property
    def config(self):
        return json.loads(rds.get(self.gen_config_yaml_key % self.id))

    def gen_config_yaml(self):
        d = {}
        services = self.app_yaml.get('services', [])
        config_yaml = self.config_yaml.copy()
    
        for service in services:
            d.update({service: get_service_config(service)})
            config_yaml.update(d)
        rds.set(self.gen_config_yaml % self.id, json.dumps(config_yaml))
    
