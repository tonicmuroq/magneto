# coding: utf-8

import json
from docker import Client

from magneto.nginx import update_nginx

"""
部署过程:

    1. consumer检查部署队列里有没有任务
    2. 获取部署任务
    3. 拿到对应的部署配置
    4. 按照部署配置部署docker container
    5. container启动成功则更新nginx配置, 重启nginx
    6. 部署完毕调用部署中心的回调接口, 告诉中心部署成功/失败
    7. 根据节点情况调用中心重启nginx的回调接口
"""


def deploy_all(app, deploy_configs):
    """
    执行一个app下的所有部署任务.
    如果是第一次在这个节点执行则需要重启中心nginx.
    全部部署成功后重启这个节点上的nginx.
    """
    containers = set()
    need_restart_center_nginx = False

    for c, deploy_config in enumerate(deploy_configs):
        app_info = deploy_config['app_info']
        cs = app_info.get('containers', [])
        host = app_info['host']
        port = app_info['port']

        # 第一个任务的时候这个节点还没有container
        if c == 0 and not cs:
            need_restart_center_nginx = True

        if deploy_one_task(deploy_config):
            cs.append('%s:%s' % (host, port))
            containers.update(set(cs))

    update_nginx(app, containers)
    if need_restart_center_nginx:
        nginx_callback()


def deploy_one_task(deploy_config):
    """
    deploy_config: 一个json, 保存了部署参数要求.

        {
            "app_info": {
                "name": "name",
                "image": "image",
                "version": "version",
                "containers": [
                    "10.1.201.16:49155",
                    "10.1.201.16:49157",
                    "10.1.201.16:49158",
                ],
                "port": port,
                "host": host,
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
    deploy_config = json.loads(deploy_config)

    # app_info 是最基本需要的
    if not 'app_info' in deploy_config:
        return False

    app = deploy_config['app_info']['name']
    image = deploy_config['app_info']['image']
    host = deploy_config['app_info']['host']
    port = deploy_config['app_info']['port']
    version = deploy_config['app_info']['version']

    container_config = deploy_config.get('container_config', {})
    runtime_config = deploy_config.get('runtime_config', {})

    container_id = deploy_container(image, container_config, runtime_config)
    if not container_id:
        return False
    
    register_callback(app, version, container_id, host, port)
    return True


def deploy_container(image, container_config, runtime_config):
    client = Client()
    if not client.ping() == 'OK':
        return None
    
    client.pull(image)
    r = client.create_container(image, container_config)
    container_id = r['Id']
    client.start(container_id, runtime_config)
    status = client.inspect_container(container_id)
    if not status['State']['Running']:
        return None
    return container_id


def register_callback(app, version, container_id, host, port):
    """告诉master这个app的version版本已经在host上
    部署了一个expose端口为port的container"""
    pass


def nginx_callback():
    pass
