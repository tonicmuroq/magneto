# coding: utf-8

from docker import Client

from magneto.nginx import update_nginx
from magneto.utils.docker import get_containers_port_of_app
from magneto.utils.decorators import docker_alive


client = Client()
host = '' # 本机的对外地址


def deploy_all(app, deploy_configs):
    """
    1. 部署container
    2. 重启本节点nginx
    """
    for deploy_config in deploy_configs:
        single_deploy_task(deploy_config)
    ports = get_containers_port_of_app(app)
    containers = ['%s:%s' % (host, p) for p in ports]
    update_nginx(app, containers)


def remove_all(app, deploy_configs):
    """
    1. 重启本机nginx
    2. 把需要下线的下线
    """
    ports = get_containers_port_of_app(app)
    containers = {'%s:%s' % (host, p) for p in ports}
    to_be_removed = set()

    for deploy_config in deploy_configs:
        app_info = deploy_config['app_info']
        cs = app_info.get('containers', [])
        removed_container = '{host}:{port}'.format(**app_info)

        containers.update(set(cs))
        to_be_removed.add(removed_container)

    remaining_containers = containers - to_be_removed
    update_nginx(app, remaining_containers)

    for deploy_config in deploy_configs:
        single_remove_task(deploy_config)


def single_deploy_task(deploy_config):
    """部署单个任务, 返回是否部署成功.
    部署成功的话需要往回注册部署信息."""
    app_info = deploy_config['app_info']
    image = app_info['image']

    container_config = deploy_config.get('container_config', {})
    runtime_config = deploy_config.get('runtime_config', {})

    container_id = add_container(image, container_config, runtime_config)
    if not container_id:
        return False
    return True


def single_remove_task(deploy_config):
    app_info = deploy_config['app_info']
    container_id = app_info['container_id']

    if stop_container(container_id):
        remove_container(container_id)
        return True
    return False


@docker_alive(client, fail_retval=None)
def add_container(image, container_config, runtime_config):
    client.pull(image)
    r = client.create_container(image, container_config)
    container_id = r['Id']
    client.start(container_id, runtime_config)
    status = client.inspect_container(container_id)
    if not status['State']['Running']:
        return None
    return container_id


@docker_alive(client)
def stop_container(container_id):
    client.stop(container_id)
    return True


@docker_alive(client)
def restart_container(container_id):
    client.restart(container_id)
    return True


@docker_alive(client)
def remove_container(container_id):
    client.remove_container(container_id) # should -v -l be flagged?
    return True
