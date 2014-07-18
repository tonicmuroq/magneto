# coding: utf-8

import gevent
import redis
import json


class Master(object):

    def __init__(self, channel, workers=[], **redis_config):
        self.workers = []
        self.redis = redis.Redis(redis_config)
        self.channel = channel

    def register(self, worker):
        self.workers.append(worker)

    def run(self):
        gevent.joinall([
            gevent.spawn(self._dispatch_task),
            gevent.spawn(self._restart_nginx),
        ])

    def _dispatch_task(self):
        while 1:
            job = self.redis.lpop(self.channel)
            if job is None:
                gevent.sleep(1)
            
            r = json.loads(job)
            host = r['host']
            if host in self.workers:
                self.redis.lpush(host, job)

    def _restart_nginx(self):
        while 1:
            job = self.redis.lpop('restart-nginx')
            if job is None:
                gevent.sleep(1)
            # restart nginx
