# coding: utf-8

import redis


class RedisBlockQueue(object):
    """一个依赖redis的特殊队列, 不能同时put和get.
    用于任务的分发, 队列满的时候做一次分发, 同时put会被阻塞.
    """

    def __init__(self, name, size, namespace='redis',
            redis_instance=None, **redis_config):
        if redis_instance:
            self._rds = redis_instance
        else:
            self._rds = redis.Redis(**redis_config)
        self.size = size
        self.key = '%s:%s' % (namespace, name)
        self._lock = self._rds.lock(self.key+':lock', timeout=120, sleep=1)

    def qsize(self):
        with self._lock:
            return self._rds.llen(self.key)

    def empty(self):
        return self.qsize() == 0

    def full(self):
        return self.qsize() == self.size

    def put(self, item):
        with self._lock:
            self._rds.rpush(self.key, item)

    def get_all(self):
        size = self.qsize()
        rs = []
        with self._lock:
            while size:
                rs.append(self._rds.lpop(self.key))
                size -= 1
            return filter(None, rs)
