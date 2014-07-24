# coding: utf-8

from sqlalchemy.ext.declarative import declarative_base

from magneto.libs.store import engine

Base = declarative_base()


def create_tables():
    Base.metadata.create_all(engine)
