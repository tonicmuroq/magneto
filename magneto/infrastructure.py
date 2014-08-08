# coding: utf-8

import os
from subprocess import check_call

from magneto.config import LEVI_NGINX_PORT, MAGNETO_NGINX_BIN, MAGNETO_NGINX_CONF_DIR, KIBANA_CONF_DIR
from magneto.utils.ensure import ensure_file, ensure_file_absent
from magneto.templates import template


def nginx_reload():
    check_call([MAGNETO_NGINX_BIN, '-s', 'reload'])


def update_nginx_config(app):
    master_nginx_conf = create_master_nginx_conf_for_app(app)
    conf_file = os.path.join(MAGNETO_NGINX_CONF_DIR, '{0}.conf'.format(app.name))
    if not master_nginx_conf:
        ensure_file_absent(conf_file)
    else:
        ensure_file(conf_file, content=master_nginx_conf)


def create_master_nginx_conf_for_app(app):
    from magneto.helper import get_hosts_for_app
    hosts = get_hosts_for_app(app)
    if not hosts:
        return ''
    master_nginx_conf = template.render_template('/levi-nginx.jinja',
            appname=app.name, hosts=hosts, port=LEVI_NGINX_PORT)
    return master_nginx_conf


def create_kibana_conf_for_app(app):
    # create app-access.json
    access_conf_name = os.path.join(KIBANA_CONF_DIR, '{0}-access.json'.format(app.name))
    access_conf = template.render_template('/nbe-accesslog.jinja', appname=app.name)
    ensure_file(access_conf_name, content=access_conf)

    # create app-app.json
    app_conf_name = os.path.join(KIBANA_CONF_DIR, '{0}-app.json'.format(app.name))
    app_conf = template.render_template('/nbe-applog.jinja', appname=app.name)
    ensure_file(app_conf_name, content=app_conf)
