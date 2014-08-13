# coding: utf-8

import json
import uuid
import time
import logging
from datetime import datetime, timedelta

from tornado import websocket
from tornado.options import options

from magneto.libs.store import taskqueue, tasklock
from magneto.libs.consts import ADD_CONTAINER, REMOVE_CONTAINER, UPDATE_CONTAINER
from magneto.libs.log import get_logger

from magneto.models.task import Task
from magneto.models.container import Container
from magneto.models.application import Application
from magneto.models.host import Host

from magneto.infrastructure import nginx_reload, update_nginx_config, create_kibana_conf_for_app
from magneto.utils.ensure import ensure_dir


level = logging.DEBUG if options.debug else logging.INFO
logger = get_logger(__name__, level=level)


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

        Host.register(self.host)
        logger.info('new host %s is registered', self.host)

    def on_message(self, data):
        '''
        * 返回值是一个dict: 部署任务结果, key是任务的uuid, value是对应任务列表完成情况.
                            成功返回cid, 失败返回''.
        * 返回值是一个list: docker container status, 每一项是一个status的dict.
        '''
        response  = json.loads(data)
        if isinstance(response, dict):
            tasks = task_wait[self.host]
            app_ids = set()
            for task_uuid, res_list in response.iteritems():
                tasks.pop(task_uuid, None)
                for task, cid in zip(Task.get_by_uuid(task_uuid), res_list):
                    app_ids.add(task.app_id)
                    if task.type == ADD_CONTAINER:
                        Container.create(cid, task.host_id, task.app_id, task.config['bind'], task.config['daemon'])
                        task.done()
                    elif task.type == REMOVE_CONTAINER:
                        if cid:
                            c = Container.get_by_cid(task.cid)
                            c.delete()
                        task.done()
                    elif task.type == UPDATE_CONTAINER:
                        if cid:
                            c = Container.get_by_cid(task.cid)
                            c.delete()
                            Container.create(cid, task.host_id, task.app_id, task.config['bind'], task.config['daemon'])
                        task.done()
            # 这次任务全部完成, 重启nginx
            if check_tasks_wait():
                logger.info('all tasks done')
                tasklock.release()
                restart_nginx(app_ids)

        elif isinstance(response, list):
            for status in response:
                cid = status['Id']
                container = Container.get_by_cid(cid)
                if container:
                    container.status = status

    def on_pong(self, data):
        health_timestamp[self.host] = datetime.now()

    def on_close(self):
        clients.pop(self.host, None)
        health_timestamp.pop(self.host, None)


def restart_nginx(app_ids):
    apps = [Application.get(i) for i in app_ids]
    for app in apps:
        update_nginx_config(app)
        create_kibana_conf_for_app(app)
    nginx_reload()
    logger.info('restart-nginx')


def check_tasks_wait():
    for host, lock_dict in task_wait.iteritems():
        if lock_dict:
            return False
    return True


def ping_clients():
    for host, last_check_timestamp in health_timestamp.iteritems():
        if datetime.now() - last_check_timestamp > timedelta(seconds=60):
            logger.warn('%s is disconnected', host)
            health_timestamp.pop(host, None)

    for host, client in clients.iteritems():
        client.ping(bytes(host))


def dispatch_task(tasks):
    logger.debug(tasks)
    if not clients or not tasks:
        tasklock.release()
        return

    deploys = {}

    for task in tasks:
        name = task['name']
        host = task['host']
        type_ = task['type']
        uid = task['uid']
        deploys.setdefault((name, host, uid, type_), []).append(task)
        ensure_dir('/mnt/mfs/permdirs/%s' % name, uid, uid)
    
    for (name, host, uid, type_), task_list in deploys.iteritems():
        task_id = str(uuid.uuid4())
        chat = {
            'name': name,
            'id': task_id,
            'uid': uid,
            'type': type_,
            'tasks': task_list,
        }

        ohost = Host.get_by_ip(host)
        # save tasks
        for seq_id, task in enumerate(task_list):
            app = Application.get_by_name_and_version(name, task['version'])
            cid = task['container'] if type_ in (REMOVE_CONTAINER, UPDATE_CONTAINER) else ''
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
                logger.debug('full check')
                dispatch_task(taskqueue.get_all())
                break
            else:
                logger.debug('full check blocked')
                time.sleep(5)


def check_taskqueue():
    if tasklock.acquire(blocking=False):
        logger.debug('time check')
        dispatch_task(taskqueue.get_all())
    else:
        logger.debug('time check blocked')
    return
