# coding: utf-8

from magneto.master import put_task
from magneto.models.container import Container
from magneto.models.host import Host
from magneto.models.task import (
    task_update_container,
    task_add_container,
    task_add_containers,
    task_remove_container,
)


def deploy_app_on_hosts(app, hosts):
    all_tasks = []
    for host in hosts:
        containers = Container.get_multi_by_host_and_appname(host.id, app.name)
        if containers:
            tasks = [task_update_container(c, app) for c in containers]
            all_tasks.extend(tasks)
        else:
            if len(app.cmd) == 1:
                all_tasks.append(task_add_container(app, host))
            elif len(app.cmd) > 1:
                all_tasks.extend(task_add_containers(app, host))
    put_task(all_tasks)


def add_app_on_host(app, host, daemon=False):
    put_task(task_add_container(app, host, daemon=daemon))


def remove_app_from_hosts(app, hosts):
    all_tasks = []
    for host in hosts:
        containers = Container.get_multi_by_host_and_app(host.id, app.id)
        if containers:
            tasks = [task_remove_container(c) for c in containers]
            all_tasks.extend(tasks)
    put_task(all_tasks)


def remove_container(container):
    put_task(task_remove_container(container))


def get_hosts_for_app(app):
    containers = Container.get_multi_by_appid(app.id)
    host_ids = set([c.host_id for c in containers if c and not c.daemon_id])
    hosts = [Host.get(i) for i in host_ids]
    return filter(None, hosts)
