# coding: utf-8

import json
from docker import Client

from magneto.nginx import update_nginx
from magneto.utils.decorators import docker_alive

"""
部署过程:

    1. consumer检查部署队列里有没有任务
    2. 获取部署任务
    3. 拿到对应的部署配置
    4. 按照部署配置部署docker container
    5. container启动成功则更新nginx配置, 重启nginx
    6. 部署完毕调用部署中心的回调接口, 告诉中心部署成功/失败
    7. 根据节点情况调用中心重启nginx的回调接口

部署配置:

    {
        "type": "add",  # add/remove
        "app_info": {
            "name": "name",
            "image": "image",
            "version": "version",
            "port": port,
            "host": host,
            "container_id": container_id, // stop/restart/remove
        },
        "container_config": {
            "entrypoint": entrypoint,
            "mem_limit": mem_limit,
            "cpu_shares": cpu_shares,
            ...
        },
        "runtime_config": {
            "port_bindings": {
                container_port1: host_port1,
                container_port2: host_port2,
                container_port3: host_port3,
                ...
            },
            "binds" = {
                container_dir1: {
                    "bind": host_dir1,
                    "ro": false,
                },
                container_dir2: {
                    "bind": host_dir2,
                    "ro": true,
                },
            },
        }
    }

    其中container_config是create_container所接受的**kwargs,
        runtime_config是start一个container所接受的**kwargs.
"""


client = Client()


def deploy_all(app, deploy_configs):
    """
    1. 如果第一个task还没有container, 需要重启master nginx
    2. 部署container
    3. 重启本节点nginx
    4. 根据1来看是否需要重启master nginx
    """
    containers = set()
    need_restart_center_nginx = False

    for c, deploy_config in enumerate(deploy_configs):
        app_info = deploy_config['app_info']
        cs = app_info.get('containers', [])
        deployed_container = '{host}:{port}'.format(**app_info)

        # 第一个任务的时候这个节点还没有container
        if c == 0 and not cs:
            need_restart_center_nginx = True

        if single_deploy_task(deploy_config):
            cs.append(deployed_container)
            containers.update(set(cs))

    update_nginx(app, containers)
    if need_restart_center_nginx:
        nginx_callback()


def remove_all(app, deploy_configs):
    """
    1. 统计本节点现在有多少container
    2. 统计要下线多少个container
    3. 如果全部下线, 则需要重启master nginx
    4. 重启本机nginx
    5. 把需要下线的下线
    """
    containers = set()
    to_be_removed = set()

    for deploy_config in deploy_configs:
        app_info = deploy_config['app_info']
        cs = app_info.get('containers', [])
        removed_container = '{host}:{port}'.format(**app_info)

        containers.update(set(cs))
        to_be_removed.add(removed_container)

    if containers == to_be_removed:
        nginx_callback()

    remaining_containers = containers - to_be_removed
    update_nginx(app, remaining_containers)

    for deploy_config in deploy_configs:
        single_remove_task(deploy_config)


def single_deploy_task(deploy_config):
    """部署单个任务, 返回是否部署成功.
    部署成功的话需要往回注册部署信息."""
    deploy_config = json.loads(deploy_config)

    # app_info 是最基本需要的
    if not 'app_info' in deploy_config:
        return False

    app_info = deploy_config['app_info']
    image = app_info['image']

    container_config = deploy_config.get('container_config', {})
    runtime_config = deploy_config.get('runtime_config', {})

    container_id = add_container(image, container_config, runtime_config)
    if not container_id:
        return False
    
    app_info['container_id'] = container_id
    register_callback(app_info, action='add')
    return True


def single_remove_task(deploy_config):
    deploy_config = json.loads(deploy_config)

    app_info = deploy_config['app_info']
    container_id = app_info['container_id']

    if stop_container(container_id):
        remove_container(container_id)
        register_callback(app_info, action='remove')
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


def register_callback(app_info, action=''):
    pass


def nginx_callback():
    """告诉master重启nginx"""
    pass
