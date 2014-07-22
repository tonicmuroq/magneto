# coding: utf-8

import json
import uuid
from datetime import datetime, timedelta

from tornado import ioloop, web, websocket

INTERVAL = 5
clients = {}
health_timestamp = {}
task_wait = {}

class MasterHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super(websocket.WebSocketHandler, self).__init__(*args, **kwargs)
        self.host = ''

    def open(self, *args):
        self.host = self.get_argument('host')
        self.stream.set_nodelay(True)
        clients[self.host] = self

    def on_message(self, ws, data):
        d = json.loads(data)
        if d['type'] == 'done' and d['id'] in task_wait:
            del task_wait[d['id']]
            # task done
            # reload nginx, etc.
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
            task_wait[task_id] = 1


app = web.Application([
    (r'/ws', MasterHandler),
])
app.listen(8881)
instance = ioloop.IOLoop.instance()
heartbeat = ioloop.PeriodicCallback(ping_clients, 1000*INTERVAL, io_loop=instance)

heartbeat.start()
instance.start()
