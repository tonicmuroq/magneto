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
