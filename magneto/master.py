# coding: utf-8

import sys
import json
import uuid
import time
import logging
from datetime import datetime, timedelta

from tornado import websocket
from websocket import create_connection

from magneto.libs.store import rds
from magneto.models.task import Task
from magneto.models.container import Container
from magneto.models.application import Application
from magneto.models.host import Host
from magneto.utils.queue import RedisBlockQueue

logger = logging.getLogger('deploy-master')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

clients = {}
health_timestamp = {}
task_wait = {}

_lock = rds.lock('dispatch-lock', timeout=115, sleep=5)
local_task_queue = RedisBlockQueue('task_queue', 15, redis_instance=rds)
ws = create_connection('ws://localhost:8882/ws')

class MasterHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super(websocket.WebSocketHandler, self).__init__(*args, **kwargs)
        self.host = ''

    def open(self, *args):
        self.host = self.get_argument('host')
        # self.host = self.request.remote_ip
        self.stream.set_nodelay(True)

        clients[self.host] = self
        task_wait[self.host] = {}

        logger.info('new host %s registered', self.host)

    def on_message(self, data):
        rep  = json.loads(data)
        if isinstance(rep, dict):
            # task done
            # reload nginx, etc.
            tasks = task_wait[self.host]
            
            # update database
            for uuid_, res_list in rep.iteritems():
                tasks.pop(uuid_, None)
                ts = Task.get_by_uuid(uuid_)
                for t, rs in zip(ts, res_list):
                    if t.type == 'add':
                        Container.create(rs, t.host_id, t.app_id, t.config['port'])
                        t.done()
                    elif t.type == 'remove':
                        if rs:
                            c = Container.get_by_cid(t.cid)
                            c.delete()
                        t.done()
                    elif t.type == 'update':
                        if rs:
                            c = Container.get_by_cid(t.cid)
                            c.delete()
                            Container.create(rs, t.host_id, t.app_id, t.config['port'])
                        t.done()

        elif isinstance(rep, list):
            for status in rep:
                cid = status['Id']
                port = status['Ports']['PublicPort']
                container = Container.get_by_cid(cid)
                if container:
                    container.status = status

        # 这次任务全部完成, 重启nginx
        if check_tasks_wait():
            logger.info('all tasks done')
            _lock.release()
            restart_nginx()

    def on_pong(self, data):
        # if self.request.remote_ip == self.host:
        if data == self.host:
            health_timestamp[self.host] = datetime.now()

    def on_close(self):
        if self.host in clients:
            del clients[self.host]


def restart_nginx():
    logger.info('restart-nginx')


def check_tasks_wait():
    for host, lock_dict in task_wait.iteritems():
        if lock_dict:
            return False
    return True


def ping_clients():
    for host, last_check_timestamp in health_timestamp.iteritems():
        if datetime.now() - last_check_timestamp > timedelta(seconds=30):
            logger.error('%s is disconnected', host)

    for host, client in clients.iteritems():
        client.ping(bytes(host))


def dispatch_task(tasks):
    if not clients:
        return

    deploys = {}
    tasks = [json.loads(t) for t in tasks]

    for task in tasks:
        name = task['name']
        host = task['host']
        type_ = task['type']
        deploys.setdefault((name, host, type_), []).append(task)
    
    for (name, host, type_), task_list in deploys.iteritems():
        task_id = str(uuid.uuid4())
        chat = {
            'name': name,
            'id': task_id,
            'type': type_,
            'tasks': task_list,
        }

        ohost = Host.get_by_ip(host)
        # save tasks
        for seq_id, task in enumerate(task_list):
            app = Application.get_by_name_and_version(name, task['version'])
            cid = task['container'] if type_ in ('remove', 'update') else ''
            Task.create(task_id, seq_id, type_, app.id, ohost.id, cid, task)

        client = clients.get(host, None)
        if client:
            client.write_message(json.dumps(chat))
            task_wait[host][task_id] = 1
        else:
            logger.warn('%s not registered, maybe problem occurred?', host)


def receive_tasks():
    while 1:
        # full, dispatch
        if local_task_queue.full():
            # still blocking, wait another 5 seconds
            if _lock.acquire(blocking=False):
                logger.info('full check')
                dispatch_task(local_task_queue.get_all())
            else:
                logger.info('full check blocked')
                time.sleep(5)

        # 假设现在只发task
        task = ws.recv()
        local_task_queue.put(task)        


def check_local_task_queue():
    # if still blocking, do nothing
    if _lock.acquire(blocking=False):
        logger.info('time check')
        dispatch_task(local_task_queue.get_all())
    else:
        logger.info('time check blocked')
    return
