# coding: utf-8

import os
import requests
from subprocess import check_call

from magneto.config import LEVI_NGINX_PORT, MAGNETO_NGINX_BIN, MAGNETO_NGINX_CONF_DIR, MAGNETO_NGINX_URL, KIBANA_CONF_DIR
from magneto.utils.ensure import ensure_file, ensure_file_absent
from magneto.templates import template


_UPSTREAM_TMPL = 'server {ip}:{port};'
_UPSTREAM_URL = 'http://%s/upstream/%s'


def nginx_reload():
    check_call([MAGNETO_NGINX_BIN, '-s', 'reload'])


def update_nginx_config(app):
    master_nginx_conf = _create_master_nginx_conf_for_app(app)
    conf_file = os.path.join(MAGNETO_NGINX_CONF_DIR, '{0}.conf'.format(app.name))
    if not master_nginx_conf:
        ensure_file_absent(conf_file)
        _delete_nginx_dynamic_upstream(app)
    else:
        ensure_file(conf_file, content=master_nginx_conf)
        _create_nginx_dynamic_upstream(app)


def create_kibana_conf_for_app(app):
    # create app-access.json
    access_conf_name = os.path.join(KIBANA_CONF_DIR, '{0}-access.json'.format(app.name))
    access_conf = template.render_template('/nbe-accesslog.jinja', appname=app.name)
    ensure_file(access_conf_name, content=access_conf)

    # create app-app.json
    app_conf_name = os.path.join(KIBANA_CONF_DIR, '{0}-app.json'.format(app.name))
    app_conf = template.render_template('/nbe-applog.jinja', appname=app.name)
    ensure_file(app_conf_name, content=app_conf)


def _create_master_nginx_conf_for_app(app):
    from magneto.helper import get_hosts_for_app
    hosts = get_hosts_for_app(app)
    if not hosts:
        return ''
    master_nginx_conf = template.render_template('/levi-nginx.jinja',
            appname=app.name, hosts=hosts, port=LEVI_NGINX_PORT)
    return master_nginx_conf


def _create_nginx_dynamic_upstream(app):
    from magneto.helper import get_hosts_for_app
    hosts = get_hosts_for_app(app)
    if not hosts:
        return False
    upstream = ''.join(_UPSTREAM_TMPL.format(ip=h.ip, port=LEVI_NGINX_PORT) for h in hosts if h)
    r = requests.post(_UPSTREAM_URL % (MAGNETO_NGINX_URL, app.name), data=upstream)
    return r.status_code == 200


def _delete_nginx_dynamic_upstream(app):
    if not app:
        return False
    r = requests.delete(_UPSTREAM_URL % (MAGNETO_NGINX_URL, app.name))
    return r.status_code == 200
