# coding: utf-8

import inspect
import functools


def namespaced_function(namespace):
    def _namespace_function(f):
        argnames, varargs, kwargs, defaults = inspect.getargspec(f)
        @functools.wraps(f)
        def _(*a, **kw):
            acopy = list(a)
            kwcopy = kw.copy()
            if argnames and len(argnames) > 1 and argnames[1] in ('key', 'name'):
                acopy[0] = '%s:%s' % (namespace, acopy[0])
            if 'key' in kwcopy:
                kwcopy['key'] = '%s:%s' % (namespace, kwcopy['key'])
            if 'name' in kwcopy:
                kwcopy['name'] = '%s:%s' % (namespace, kwcopy['name'])
            if varargs == 'names':
                acopy = ['%s:%s' % (namespace, i) for i in acopy]
            return f(*acopy, **kwcopy)
        return _
    return _namespace_function


class NamespacedRedis(object):

    def __init__(self, redis, namespace=''):
        self._redis = redis
        self._namespace = namespace

    def __getattr__(self, name):
        redis_method = getattr(self._redis, name)
        return namespaced_function(self._namespace)(redis_method)
