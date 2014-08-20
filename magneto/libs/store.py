# coding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
try:
    from sqlalchemy.orm.scoping import scoped_session
except ImportError:
    from sqlalchemy.orm.scoping import ScopedSession as scoped_session

import redis
from redis.lock import Lock

from .queue import RedisBlockQueue
from .deco import NamespacedRedis
from magneto.config import DATABASE_URI, REDIS_HOST, REDIS_PORT

engine = create_engine(DATABASE_URI)
session = scoped_session(sessionmaker(bind=engine))

rds = NamespacedRedis(redis.Redis(host=REDIS_HOST, port=REDIS_PORT), 'magneto')
taskqueue = RedisBlockQueue('taskqueue', 15, redis_instance=rds)
tasklock = rds.lock('redis:tasklock', lock_class=Lock, timeout=120, sleep=5)
