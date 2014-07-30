# coding: utf-8

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
    check_taskqueue,
)

create_tables()

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
check_queue = ioloop.PeriodicCallback(check_taskqueue, 25000, io_loop=instance)

for ins in (heartbeat, check_queue, instance):
    ins.start()
