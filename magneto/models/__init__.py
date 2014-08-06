# coding: utf-8

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError

from magneto.libs.store import engine

Base = declarative_base()


def create_tables():
    # 注册到SQLAlchemy
    from magneto.models.application import Application
    from magneto.models.host import Host
    from magneto.models.user import User
    from magneto.models.container import Container
    from magneto.models.task import Task
    Base.metadata.create_all(engine)


def create_data():
    from .host import Host
    from .application import Application

    Host.create('10.1.201.16', '16host')
    Host.create('10.1.201.17', '17host')

    Application.create('dalaran', 'version', '{"appname": "app", "version": "version"}')
    Application.create('icecrown', 'version', '{"appname": "app", "version": "version"}')
    Application.create('ulduar', 'version', '{"appname": "app", "version": "version"}')
