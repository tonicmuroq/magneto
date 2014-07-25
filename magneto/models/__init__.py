# coding: utf-8

from sqlalchemy.ext.declarative import declarative_base

from magneto.libs.store import engine

Base = declarative_base()


def create_tables():
    Base.metadata.create_all(engine)


def create_data():
    from .host import Host
    from .application import Application

    Host.create('10.1.201.16', '16host')
    Host.create('10.1.201.17', '17host')

    Application.create('dalaran', 'version')
    Application.create('icecrown', 'version')
    Application.create('ulduar', 'version')
