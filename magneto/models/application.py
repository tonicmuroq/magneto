# coding: utf-8

import json
import random
import string
import sqlalchemy as db

from magneto.libs.store import session, rds
from magneto.models import Base, IntegrityError, OperationalError
from magneto.mysql import setup_mysql
from magneto.config import MYSQL_CONFIG, REDIS_HOST, REDIS_PORT


def _redis_service(app):
    # TODO 用真实的redis
    return {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
    }


def _mysql_service(app):
    host = MYSQL_CONFIG['host']
    port = MYSQL_CONFIG['port']
    return {
        'host': host,
        'post': port,
        'username': app.name,
        'password': app.mysql_password,
    }


SERVICE_CONFIGS = {
    'redis': _redis_service,
    'mysql': _mysql_service,
}


class Application(Base):

    __tablename__ = 'application'
    __table_args__ = db.UniqueConstraint('name', 'version', name='uk_name_version'),
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(100), nullable=False)
    pname = db.Column(db.String(50), nullable=False)

    app_yaml_key = 'app:app_yaml:%s'
    config_yaml_key = 'app:config_yaml:%s'
    gen_config_yaml_key = 'app:gen_config_yaml:%s'
    app_mysql_key = 'app:mysql:dbkey:%s'
    app_schema_key = 'app:schema:dbkey:%s'

    @classmethod
    def create(cls, name, version, app_yaml=None, config_yaml=None):
        if not app_yaml:
            return None
        if not config_yaml:
            config_yaml = '{}'

        try:
            app_yaml_dict = json.loads(app_yaml)
        except:
            return None
        aname = app_yaml_dict.get('appname', name)

        app = cls(name=aname, version=version, pname=name)
        try:
            session.add(app)
            session.commit()
        except (IntegrityError, OperationalError):
            session.rollback()
            return None

        rds.set(app.app_yaml_key % app.id, app_yaml)
        rds.set(app.config_yaml_key % app.id, config_yaml)

        app.gen_config_yaml()

        return app

    @classmethod
    def get(cls, id):
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_multi_by_name(cls, name):
        return session.query(cls).filter(cls.name == name).all()

    @classmethod
    def get_latest(cls, name):
        return session.query(cls).filter(cls.name == name).\
                order_by(cls.id.desc()).first()

    @classmethod
    def get_by_name_and_version(cls, name, version):
        if version == 'latest':
            return cls.get_latest(name)
        return session.query(cls).filter(cls.name == name).\
                filter(cls.version == version).first()

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
        cmd = self.app_yaml.get('cmd', [])
        return cmd

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

    def _get_schema(self):
        return rds.get(self.app_schema_key % self.name)
    def _set_schema(self, schema):
        rds.set(self.app_schema_key % self.name, schema)
    schema = property(_get_schema, _set_schema)

    def gen_config_yaml(self):
        d = {}
        services = self.app_yaml.get('services', [])
        config_yaml = self.config_yaml.copy()
    
        for service in services:
            d.update({service: SERVICE_CONFIGS.get(service, lambda app:{})(self)})
            config_yaml.update(d)
        rds.set(self.gen_config_yaml_key % self.id, json.dumps(config_yaml))

    def setup_database(self):
        key = self.app_mysql_key % self.name
        if rds.get(key):
            return
        passwd = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        setup_mysql(self.name, passwd)

        rds.set(key, json.dumps([passwd, '']))

    def setup_schema(self):
        pass

