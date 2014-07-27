# coding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session

import redis

engine = create_engine('sqlite:///magneto.db')
session = scoped_session(sessionmaker(bind=engine))

rds = redis.Redis()
