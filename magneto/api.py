# coding: utf-8

import tornado

from magneto.libs.store import taskqueue

from magneto.models.application import Application
from magneto.models.host import Host 
from magneto.models.container import Container
from magneto.models.task import task_add_container, task_remove_container, task_update_container


class GetAppAPIHandler(tornado.web.RequestHandler):

    def get(self, name, version):
        app = Application.get_by_name_and_version(name, version)
        if not app:
            self.write({'r': 1, 'msg': 'no such app'})
        else:
            self.write({'r': 0})


class AddAppAPIHandler(tornado.web.RequestHandler):

    def post(self):
        name = self.get_body_argument('app_name')
        version = self.get_body_argument('app_version')
        app_yaml = self.get_body_argument('app_yaml')
        config_yaml = self.get_body_argument('config_yaml', default=None)
        Application.create(name, version, app_yaml, config_yaml)
        self.write({'r': 0})


class AddHostAPIHandler(tornado.web.RequestHandler):

    def post(self):
        ip = self.get_body_argument('host')
        name = self.get_body_argument('name', default='')
        host = Host.create(ip, name)
        if not host:
            self.write({'r': 1, 'msg': 'error'})
        else:
            self.write({'r': 0})


class DeployAppAPIHandler(tornado.web.RequestHandler):

    def post(self):
        app = self.get_body_argument('app', '')
        host = self.get_body_argument('host', '')
        action = self.get_body_argument('action')
        container = self.get_body_argument('container', '')

        app = Application.get(app)
        host = Host.get(host)

        if not (app and host):
            self.write({'r': 1, 'msg': 'app/host missed'})
        else:
            if action == 'add':
                task = task_add_container(app, host)
            elif action == 'remove':
                container = Container.get_by_cid(container)
                task = task_remove_container(container)
            elif action == 'update':
                container = Container.get_by_cid(container)
                task = task_update_container(container, app)
            else:
                task = {}
            if task:
                taskqueue.put(task)
            self.write({'r': 0})
