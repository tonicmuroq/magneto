# coding: utf-8

import sys
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from Queue import Queue

from tornado import websocket
from websocket import create_connection

from magneto.libs.store import rds
from magneto.models.task import Task
from magneto.models.application import Application
from magneto.models.host import Host

logger = logging.getLogger('deploy-master')
logger.addHandler(logging.StreamHandler(sys.stdout))

clients = {}
health_timestamp = {}
task_wait = {}

_lock = rds.lock('dispatch-lock', timeout=115, sleep=5)

ws = create_connection('ws://localhost:8882/ws')
local_task_queue = Queue(maxsize=15)

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
                Task.update_multi_status(uuid_, res_list)

        elif isinstance(rep, list):
            # container status
            pass
        else:
            pass

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

        # save tasks
        app = Application.get_by_name(name)
        host = Host.get_by_ip(host)
        Task.create_multi(task_id, app.id, type_, host.id, task_list)

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
                dispatch_task(_deal_queue(local_task_queue))
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
        dispatch_task(_deal_queue(local_task_queue))
    else:
        logger.info('time check blocked')
    return


def _deal_queue(queue):
    tasks = []
    while not queue.empty():
        tasks.append(queue.get())
    return tasks
