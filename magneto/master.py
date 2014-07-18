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


def dispatch_task(tasks):
    deploys = {}
    tasks = [json.loads(t) for t in tasks]

    # step1. 按照部署目的地分组
    for task in tasks:
        app_info = task['app_info']
        deploy_dest = '{host}:{port}'.format(**app_info)
        deploys.setdefault(deploy_dest, []).append(task)
    
    # step2. 对每个部署节点上按照app分组
    # 分发出去任务
    for deploy_dest, deploy_configs in deploys.iteritems():
        configs = {}
        for deploy_config in deploy_configs:
            app_info = deploy_config['app_info']
            app = app_info['name']
            configs.setdefault(app, []).append(deploy_config)
        
        for app, dconfig in configs.iteritems():
            dispatch_tasks_to_node(deploy_dest, app, dconfig)
        

def dispatch_tasks_to_node(node, app, tasks):
    pass
