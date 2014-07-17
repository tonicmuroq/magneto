# coding: utf-8

from subprocess import check_call

from jinja2 import Environment, PackageLoader

import magneto
from magneto.utils.ensure import ensure_file


class Jinja2(object):

    def __init__(self, package_name, template_folder='templates'):
        self.loader = PackageLoader(package_name, template_folder)
        self.environment = Environment(loader=self.loader, autoescape=True)

    def render_template(self, template_name, **data):
        template = self.environment.get_template(template_name)
        return template.render(**data)


template = Jinja2(magneto.__name__)


def restart_nginx():
    check_call(['nginx', '-s', 'reload'])


def update_nginx(app, containers):
    """
    1. update nginx config
    2. restart nginx
    """
    nginx_conf = create_nginx_config(app, containers)
    ensure_file('/etc/nginx/conf.d/nginx_{0}.conf'.format(app), nginx_conf)
    restart_nginx()


def create_nginx_config(app, containers):
    # containers 现在是一个list
    # [
    #     '10.1.201.16:49155',
    #     '10.1.201.16:49156',
    #     '10.1.201.16:49158',
    # ]
    # TODO 封装
    nodes = containers
    backups = []
    nginx_conf = template.render_template('/app_nginx.jinja',
            app=app, nodes=nodes, backups=backups)
    return nginx_conf
