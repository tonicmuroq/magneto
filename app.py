# coding: utf-8

import threading

from tornado import web, ioloop

from magneto.master import (
    MasterHandler,
    ping_clients,
    check_local_task_queue,
    receive_tasks,
)


HANDLERS = [
    (r'/ws', MasterHandler),
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