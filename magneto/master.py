# coding: utf-8

import json
import uuid
import redis
import threading
import time
from datetime import datetime, timedelta
from Queue import Queue

from tornado import ioloop, web, websocket
from websocket import create_connection

clients = {}
health_timestamp = {}
task_wait = {}

r = redis.Redis()
_lock = r.lock('dispatch-lock', timeout=115, sleep=5)

ws = create_connection('ws://localhost:8882/ws')
local_task_queue = Queue(maxsize=15)

class MasterHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super(websocket.WebSocketHandler, self).__init__(*args, **kwargs)
        self.host = ''

    def open(self, *args):
        self.host = self.get_argument('host')
        self.stream.set_nodelay(True)
        clients[self.host] = self
        task_wait[self.host] = {}
        print 'new host %s registered' % self.host

    def on_message(self, data):
        d = json.loads(data)
        if d['type'] == 'done':
            # task done
            # reload nginx, etc.
            tasks = task_wait[self.host]
            tasks.pop(d['id'], None)
        else:
            # others
            pass

        # 这次任务全部完成, 重启nginx
        if check_tasks_wait():
            print '任务全部完成'
            _lock.release()
            restart_nginx()

    def on_pong(self, data):
        if data == self.host:
            health_timestamp[self.host] = datetime.now()
        else:
            print 'not valid pong'

    def on_close(self):
        if self.host in clients:
            del clients[self.host]


def restart_nginx():
    print 'restart-nginx'


def check_tasks_wait():
    for host, lock_dict in task_wait.iteritems():
        if lock_dict:
            return False
    return True


def ping_clients():
    for host, last_check_timestamp in health_timestamp.iteritems():
        if datetime.now() - last_check_timestamp > timedelta(seconds=30):
            print '%s is disconnected' % host

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
        client = clients.get(host, None)
        if client:
            client.write_message(json.dumps(chat))
            task_wait[host][task_id] = 1
        else:
            print '%s not registered, maybe problem occurred?' % host


def receive_tasks():
    while 1:
        # full, dispatch
        if local_task_queue.full():
            # still blocking, wait another 5 seconds
            if _lock.acquire(blocking=False):
                print 'full check'
                dispatch_task(_deal_queue(local_task_queue))
            else:
                print 'full check blocked'
                time.sleep(5)

        # 假设现在只发task
        task = ws.recv()
        local_task_queue.put(task)        


def check_local_task_queue():
    # if still blocking, do nothing
    if _lock.acquire(blocking=False):
        print 'time check'
        dispatch_task(_deal_queue(local_task_queue))
    else:
        print 'time check blocked'
    return


def _deal_queue(queue):
    tasks = []
    while not queue.empty():
        tasks.append(queue.get())
    return tasks


app = web.Application([
    (r'/ws', MasterHandler),
])
app.listen(8881)

instance = ioloop.IOLoop.instance()
heartbeat = ioloop.PeriodicCallback(ping_clients, 15000, io_loop=instance)
check_queue = ioloop.PeriodicCallback(check_local_task_queue, 25000, io_loop=instance)

receive = threading.Thread(target=receive_tasks)
receive.daemon = True

if __name__ == '__main__':
    try:
        _lock.release()
    except:
        print 'lock already released'

    heartbeat.start()
    check_queue.start()
    receive.start()
    instance.start()
