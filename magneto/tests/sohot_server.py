# coding: utf-8

import time
import json
from random import choice
from tornado import ioloop, web, websocket


app_names = ['dalaran', 'icecrown', 'ulduar']
hosts = ['10.1.201.16', '10.1.201.17']
types = ['add', 'remove', 'update']


def make_task():
    task = {
        'name': choice(app_names),
        'host': choice(hosts),
        'type': choice(types),
        'image': 'image',
        'version': 'version',
        'memory': 65536,
        'cpus': 0.7,
        'entrypoint': 'gunicorn -c conf.py app:app'
    }
    return task


class SohotHandler(websocket.WebSocketHandler):

    def open(self, *args):
        self.stream.set_nodelay(True)
        while 1:
            task = make_task()
            self.write_message(json.dumps(task))
            print 'task [{name}, {host}, {type}] sent'.format(**task)
            time.sleep(1)


app = web.Application([
    (r'/ws', SohotHandler),
])
app.listen(8882)
ioloop.IOLoop.instance().start()