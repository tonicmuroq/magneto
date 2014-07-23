# coding: utf-8

import json
import uuid
import threading
from datetime import datetime, timedelta
from Queue import Queue

from tornado import ioloop, web, websocket
from websocket import create_connection

INTERVAL = 5
clients = {}
health_timestamp = {}
task_wait = {}
_lock = threading.Lock()

ws = create_connection('ws://localhost:8882/ws')
local_task_queue = Queue(maxsize=100)

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
            host = d['host']
            tasks = task_wait[host]
            tasks.pop(d['id'], None)
            if not tasks:
                print 'all tasks on %s done' % host
            else:
                print '%s tasks remaining on %s' % (len(tasks), host)
        else:
            # others
            pass

    def on_pong(self, data):
        if data == self.host:
            health_timestamp[self.host] = datetime.now()
        else:
            print 'not valid pong'

    def on_close(self):
        if self.host in clients:
            del clients[self.host]


def ping_clients():
    for host, last_check_timestamp in health_timestamp.iteritems():
        if datetime.now() - last_check_timestamp > timedelta(seconds=2*INTERVAL):
            print '%s is disconnected' % host

    for host, client in clients.iteritems():
        client.ping(bytes(host))


def dispatch_task(tasks):
    if not clients:
        return

    #with _lock:
    deploys = {}
    tasks = [json.loads(t) for t in tasks]

    for task in tasks:
        name = task['name']
        host = task['host']
        deploys.setdefault((name, host), []).append(task)
    
    for (name, host), task_list in deploys.iteritems():
        task_id = str(uuid.uuid4())
        chat = {
            'name': name,
            'id': task_id,
            'tasks': task_list,
        }
        client = clients.get(host, None)
        if client:
            client.write_message(json.dumps(chat))
            task_wait[host][task_id] = 1
            print 'task sent to %s' % host
        else:
            print '%s not registered, maybe problem occurred?' % host


def receive_tasks():
    while 1:
        # full, dispatch
        if local_task_queue.full():
            dispatch_task(_deal_queue(local_task_queue))

        # 假设现在只发task
        task = ws.recv()
        local_task_queue.put(task)        


def check_local_task_queue():
    #with _lock:
    print 'time check'
    dispatch_task(_deal_queue(local_task_queue))


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
heartbeat = ioloop.PeriodicCallback(ping_clients, 1000*INTERVAL, io_loop=instance)
check_queue = ioloop.PeriodicCallback(check_local_task_queue, 3000*INTERVAL, io_loop=instance)

receive = threading.Thread(target=receive_tasks)
receive.daemon = True

heartbeat.start()
check_queue.start()
receive.start()
instance.start()
