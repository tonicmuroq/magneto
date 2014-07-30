# coding: utf-8

import json
import random
import string
import sqlalchemy as db

from magneto.libs.store import session, rds
from magneto.models import Base, IntegrityError
from magneto.mysql import setup_mysql


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
    __table_args__ = db.UniqueConstraint('name', 'version', name='uk_name_version'),
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    pname = db.Column(db.String(50), nullable=False)

    app_yaml_key = 'app:app_yaml:%s'
    config_yaml_key = 'app:config_yaml:%s'
    gen_config_yaml_key = 'app:gen_config_yaml:%s'
    app_mysql_key = 'app:mysql:dbkey:%s'

    @classmethod
    def create(cls, name, version, app_yaml=None, config_yaml=None):
        if not app_yaml:
            return None
        if not config_yaml:
            config_yaml = '{}'

        # TODO appname hard code
        app_yaml_dict = json.loads(app_yaml)
        pname = app_yaml_dict.get('appname', name)

        app = cls(name=name, version=version, pname=pname)
        try:
            session.add(app)
            session.commit()
        except IntegrityError:
            session.rollback()
            return None

        rds.set(app.app_yaml_key % app.id, app_yaml)
        rds.set(app.config_yaml_key % app.id, config_yaml)

        app.gen_config_yaml()
        app.setup_mysql()

        return app

    @classmethod
    def get(cls, id):
        return session.query(cls).filter(cls.id == id).one()

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

    @property
    def cmd(self):
        return self.app_yaml.get('cmd', '')

    @property
    def port(self):
        return self.app_yaml.get('port', 5000)

    @property
    def _passwords(self):
        key = self.app_mysql_key % self.name
        r = rds.get(key) or '["", ""]'
        return json.loads(r)

    @property
    def mysql_password(self):
        return self._passwords[0]

    @property
    def mysql_manager_password(self):
        return self._passwords[1]

    def gen_config_yaml(self):
        d = {}
        services = self.app_yaml.get('services', [])
        config_yaml = self.config_yaml.copy()
    
        for service in services:
            d.update({service: get_service_config(service)})
            config_yaml.update(d)
        rds.set(self.gen_config_yaml_key % self.id, json.dumps(config_yaml))

    def setup_database(self):
        key = self.app_mysql_key % self.name
        if rds.get(key):
            return
        passwd = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        manager_passwd = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        setup_mysql(self.name, passwd, manager_passwd)

        rds.set(key, json.dumps([passwd, manager_passwd]))
