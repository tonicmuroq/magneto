# coding: utf-8

import gevent
import redis
import json
import websocket

from tornado import ioloop, web, websocket as twebsocket

clients = {}

class MasterHandler(twebsocket.WebSocketHandler):

    def __init__(self, url):
        self.url = url

    def run(self):
        ws = websocket.WebSocketApp(self.url,
                on_message=self.on_message)
        ws.run_forever()

    def on_message(self, ws, data):
        d = json.loads(data)
        if d['type'] in ('add', 'remove'):
            conn = self.slaves.get(d['app_info']['host'], None)
            if conn:
                conn.send(data)
        elif d['type'] == 'restart-nginx':
            restart_nginx()


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
