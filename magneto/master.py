# coding: utf-8

import json
import uuid
import time
import logging
from datetime import datetime, timedelta

from tornado import websocket

from magneto.libs.store import taskqueue, tasklock
from magneto.libs.colorlog import ColorizingStreamHandler

from magneto.models.task import Task
from magneto.models.container import Container
from magneto.models.application import Application
from magneto.models.host import Host

logging.StreamHandler = ColorizingStreamHandler
logging.BASIC_FORMAT = "%(asctime)s [%(name)s] %(message)s"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

clients = {}
health_timestamp = {}
task_wait = {}


class MasterHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super(websocket.WebSocketHandler, self).__init__(*args, **kwargs)
        self.host = ''

    def open(self, *args):
        self.host = self.request.remote_ip
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
                    if t.type == 1:
                        Container.create(rs, t.host_id, t.app_id, t.config['port'])
                        t.done()
                    elif t.type == 2:
                        if rs:
                            c = Container.get_by_cid(t.cid)
                            c.delete()
                        t.done()
                    elif t.type == 3:
                        if rs:
                            c = Container.get_by_cid(t.cid)
                            c.delete()
                            Container.create(rs, t.host_id, t.app_id, t.config['port'])
                        t.done()
            # 这次任务全部完成, 重启nginx
            if check_tasks_wait():
                logger.info('all tasks done')
                tasklock.release()
                restart_nginx()

        elif isinstance(rep, list):
            # container 状态
            for status in rep:
                cid = status['Id']
                #port = status['Ports']['PublicPort']
                container = Container.get_by_cid(cid)
                if container:
                    container.status = status

    def on_pong(self, data):
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
    logger.info(tasks)
    if not clients or not tasks:
        tasklock.release()
        return

    deploys = {}

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
            cid = task['container'] if type_ in (2, 3) else ''
            Task.create(task_id, seq_id, type_, app.id, ohost.id, cid, task)

        client = clients.get(host, None)
        if client:
            client.write_message(json.dumps(chat))
            task_wait[host][task_id] = 1
        else:
            logger.warn('%s not registered, maybe problem occurred?', host)


def put_task(task):
    if not task:
        return

    if isinstance(task, list):
        taskqueue.put_list(task)
    else:
        taskqueue.put(task)        

    if taskqueue.full():
        while 1:
            if tasklock.acquire(blocking=False):
                logger.info('full check')
                dispatch_task(taskqueue.get_all())
                break
            else:
                logger.info('full check blocked')
                time.sleep(5)


def check_taskqueue():
    if tasklock.acquire(blocking=False):
        logger.info('time check')
        dispatch_task(taskqueue.get_all())
    else:
        logger.info('time check blocked')
    return
