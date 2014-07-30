# coding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session

import redis

from .queue import RedisBlockQueue
from magneto.config import database_uri, redis_host, redis_port

engine = create_engine(database_uri)
session = scoped_session(sessionmaker(bind=engine))

rds = redis.Redis(host=redis_host, port=redis_port)
taskqueue = RedisBlockQueue('taskqueue', 15, redis_instance=rds)
tasklock = rds.lock('magneto:redis:tasklock', timeout=120, sleep=5)
