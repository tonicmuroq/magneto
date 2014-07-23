#! /usr/bin/env python
# coding: utf-8

import json
import websocket
from time import sleep
from optparse import OptionParser


def parse_args():
    parser = OptionParser()
    parser.add_option('-t', '--time', dest='time', type='int', default=1)
    parser.add_option('-d', '--host', dest='host', type='str', default='')
    options, args = parser.parse_args()
    return options.time, options.host


def run_client():
    time, host = parse_args()
    url = 'ws://localhost:8881/ws?host=%s' % host
    ws = websocket.create_connection(url)
    while 1:
        tasks = ws.recv()
        chat = json.loads(tasks)
        chat_id = chat['id']
        sleep(time)
        print 'task %s done, task count %s' % (chat_id, len(chat['tasks']))

        payload = dict(type='done', id=chat_id, host=host)
        ws.send(json.dumps(payload))


if __name__ == '__main__':
    run_client()
