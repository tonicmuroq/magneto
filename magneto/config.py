# coding: utf-8

DEV = False
MYSQL_CONFIG = {
    'user': 'platform_root',
    'passwd': 'mnjksghqFGeksh342ui',
    'host': '10.1.201.58',
    'db': 'nbe',
    'port': 3306,
}

REDIS_HOST = '10.1.201.16'
REDIS_PORT = 6379

LEVI_NGINX_PORT = 80

DNS_HOST = '10.1.201.22:9157'

MAGNETO_HOST = '10.1.201.99'
MAGNETO_NGINX_BIN = '/usr/sbin/nginx'
MAGNETO_NGINX_CONF_DIR = '/etc/nginx/conf.d'
MAGNETO_NGINX_URL = '127.0.0.1:90'
KIBANA_CONF_DIR = '/mnt/mfs/kibana/conf.d'

try:
    from local_config import *
except ImportError:
    pass

DATABASE_URI = 'mysql://{user}:{passwd}@{host}/{db}'.format(**MYSQL_CONFIG)
