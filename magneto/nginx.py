# coding: utf-8

from subprocess import check_call

from jinja2 import Environment, PackageLoader

import magneto
from magneto.utils.ensure import ensure_file, ensure_file_absent


class Jinja2(object):

    def __init__(self, package_name, template_folder='templates'):
        self.loader = PackageLoader(package_name, template_folder)
        self.environment = Environment(loader=self.loader, autoescape=True)

    def render_template(self, template_name, **data):
        template = self.environment.get_template(template_name)
        return template.render(**data)


template = Jinja2(magneto.__name__)


def nginx_reload():
    check_call(['nginx', '-s', 'reload'])


def update_nginx_config(app):
    master_nginx_conf = create_master_nginx_conf_for_app(app)
    conf_file_name = '/etc/nginx/conf.d/{0}.conf'.format(app.name)
    if not master_nginx_conf:
        ensure_file_absent(conf_file_name)
    else:
        ensure_file(conf_file_name, content=master_nginx_conf)


def create_master_nginx_conf_for_app(app):
    from magneto.helper import get_hosts_for_app
    hosts = get_hosts_for_app(app)
    if not hosts:
        return ''
    master_nginx_conf = template.render_template('/levi_nginx.jinja',
            appname=app.name, hosts=hosts)
    return master_nginx_conf
