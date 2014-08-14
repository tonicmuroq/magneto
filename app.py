# coding: utf-8

import os
import signal

from tornado import web, ioloop, options

from magneto.libs.log import get_logger
from magneto.models import create_tables


options.define('port', default=8881, type=int)
options.define('daemon', default=False, type=bool)
options.define('debug', default=False, type=bool)
options.parse_command_line()
logger = get_logger(__name__)

create_tables()

from magneto.api import (GetAppAPIHandler, AddAppAPIHandler, AddHostAPIHandler,
        DeployAppAPIHandler, RemoveAppAPIHandler, AppSchemaAPIHandler,
        AddContainerAPIHandler, RemoveContainerAPIHandler)
from magneto.master import MasterHandler, ping_clients, check_taskqueue

HANDLERS = [
    (r'/ws', MasterHandler),
    (r'/app/new', AddAppAPIHandler),
    (r'/host/new', AddHostAPIHandler),
    (r'/app/([\-\w]+)/([\-\w]+)', GetAppAPIHandler),
    (r'/app/([\-\w]+)/([\-\w]+)/deploy', DeployAppAPIHandler),
    (r'/app/([\-\w]+)/([\-\w]+)/add', AddContainerAPIHandler),
    (r'/app/([\-\w]+)/([\-\w]+)/remove', RemoveAppAPIHandler),
    (r'/app/([\-\w]+)/([\-\w]+)/schema', AppSchemaAPIHandler),
    (r'/container/([\-\w]+)/remove', RemoveContainerAPIHandler),
]

app = web.Application(HANDLERS)
app.listen(options.options.port)

instance = ioloop.IOLoop.instance()
heartbeat = ioloop.PeriodicCallback(ping_clients, 15000, io_loop=instance)
check_queue = ioloop.PeriodicCallback(check_taskqueue, 25000, io_loop=instance)


def start_magneto():
    try:
        logger.info('magneto started, %s', os.getpid())
        for ins in (heartbeat, check_queue, instance):
            ins.start()
    except:
        for ins in (heartbeat, check_queue, instance):
            ins.stop()
        logger.info('magneto stopped.')


def stop_magneto(signum, frame):
    for ins in (heartbeat, check_queue, instance):
        ins.stop()
    logger.info('magneto stopped.')


signal.signal(signal.SIGTERM, stop_magneto)
signal.signal(signal.SIGQUIT, stop_magneto)
signal.signal(signal.SIGINT, stop_magneto)


if __name__ == '__main__':
    start_magneto()
