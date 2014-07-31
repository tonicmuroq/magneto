# coding: utf-8

import tornado
from cStringIO import StringIO

from magneto.models.application import Application
from magneto.models.host import Host 

from magneto.helper import deploy_app_on_hosts, remove_app_from_hosts


_OK_RESP = {'r': 0}


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
        self.write(_OK_RESP)


class AppSchemaAPIHandler(tornado.web.RequestHandler):

    def post(self, app_name, app_version):
        app = Application.get_by_name_and_version(app_name, app_version)

        f = self.request.files['schema'][0]
        sio = StringIO()
        sio.write(f['body'])
        schema = sio.getvalue()
        app.schema = schema
        self.write(_OK_RESP)


class AddHostAPIHandler(tornado.web.RequestHandler):

    def post(self):
        ip = self.get_body_argument('host')
        name = self.get_body_argument('name', default='')
        Host.create(ip, name)
        self.write(_OK_RESP)


class DeployAppAPIHandler(tornado.web.RequestHandler):

    def post(self, app_name, app_version):
        hosts = self.get_body_arguments('hosts')
        hosts = Host.get_multi_by_ip(hosts)

        app = Application.get_by_name_and_version(app_name, app_version)
        app.setup_database()

        deploy_app_on_hosts(app, filter(None, hosts))
        self.write(_OK_RESP)


class RemoveAppAPIHandler(tornado.web.RequestHandler):

    def post(self, app_name, app_version):
        hosts = self.get_body_arguments('hosts')
        hosts = Host.get_multi_by_ip(hosts)

        app = Application.get_by_name_and_version(app_name, app_version)
        remove_app_from_hosts(app, hosts)
        self.write(_OK_RESP)
