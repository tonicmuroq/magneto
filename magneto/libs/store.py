# coding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session

import redis

from .queue import RedisBlockQueue

engine = create_engine('sqlite:///magneto.db')
session = scoped_session(sessionmaker(bind=engine))

rds = redis.Redis()
taskqueue = RedisBlockQueue('taskqueue', 15, redis_instance=rds)
