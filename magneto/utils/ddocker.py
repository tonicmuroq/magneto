# coding: utf-8

from docker import Client

from .decorators import docker_alive


client = Client()


@docker_alive(client, fail_retval=[])
def get_containers_port_of_app(app):

    def _filter_app_name(container, app):
        # Names like [app_${port},]
        names = container['Names']
        name = names and names[0] or ''
        return app in name

    def _get_public_port_of_container(container):
        ports = container['Ports']
        if ports:
            return ports[0]['PublicPort']
        return None

    containers = client.containers(trunc=False)
    ports = [_get_public_port_of_container(c) for c in containers if _filter_app_name(c, app)]
    return filter(None, ports)
