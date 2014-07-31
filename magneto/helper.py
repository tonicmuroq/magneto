# coding: utf-8

from magneto.master import put_task
from magneto.models.container import Container
from magneto.models.task import (
    task_update_container,
    task_add_container,
    task_remove_container,
)


def deploy_app_on_hosts(app, hosts):
    all_tasks = []
    for host in hosts:
        containers = Container.get_multi_by_host_and_app(host.id, app.id)
        if containers:
            tasks = [task_update_container(c, app) for c in containers]
            all_tasks.extend(tasks)
        else:
            all_tasks.append(task_add_container(app, host))
    put_task(all_tasks)


def remove_app_from_hosts(app, hosts):
    all_tasks = []
    for host in hosts:
        containers = Container.get_multi_by_host_and_app(host.id, app.id)
        if containers:
            tasks = [task_remove_container(c) for c in containers]
            all_tasks.extend(tasks)
    put_task(all_tasks)
