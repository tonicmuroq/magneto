# coding: utf-8

from functools import wraps


def docker_alive(client, fail_retval=False):
    def _docker_alive(f):
        @wraps(f)
        def _(*a, **kw):
            if not client.ping() == 'OK':
                return fail_retval
            return f(*a, **kw)
        return _
    return _docker_alive


def redis_lock(redis, name, timeout=None, sleep=0.1):
    def _redis_lock(f):
        @wraps(f)
        def _(*args, **kwargs):
            with redis.lock(name, timeout, sleep):
                return f(*args, **kwargs)
        return _
    return _redis_lock
