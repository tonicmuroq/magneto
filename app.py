# coding: utf-8

import threading

from tornado import web, ioloop

from magneto.models import create_tables, create_data
from magneto.api import (
    GetAppAPIHandler,
    AddAppAPIHandler,
    AddHostAPIHandler
)
from magneto.master import (
    MasterHandler,
    ping_clients,
    check_local_task_queue,
    receive_tasks,
)

create_tables()
create_data()

HANDLERS = [
    (r'/ws', MasterHandler),
    (r'/app/new', AddAppAPIHandler),
    (r'/app/(\w+)/(\w+)', GetAppAPIHandler),
    (r'/host/add', AddHostAPIHandler),
]

app = web.Application(HANDLERS)
app.listen(8881)

instance = ioloop.IOLoop.instance()
heartbeat = ioloop.PeriodicCallback(ping_clients, 15000, io_loop=instance)
check_queue = ioloop.PeriodicCallback(check_local_task_queue, 25000, io_loop=instance)

receive = threading.Thread(target=receive_tasks)
receive.daemon=True

for ins in (heartbeat, check_queue, receive, instance):
    ins.start()
