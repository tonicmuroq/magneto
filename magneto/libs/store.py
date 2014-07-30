# coding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session

import redis

from .queue import RedisBlockQueue
from magneto.config import DATABASE_URI, REDIS_HOST, REDIS_PORT

engine = create_engine(DATABASE_URI)
session = scoped_session(sessionmaker(bind=engine))

rds = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
taskqueue = RedisBlockQueue('taskqueue', 15, redis_instance=rds)
tasklock = rds.lock('magneto:redis:tasklock', timeout=120, sleep=5)
