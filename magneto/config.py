# coding: utf-8

DEV = False
MYSQL_CONFIG = {
    'user': 'platform_root',
    'passwd': 'mnjksghqFGeksh342ui',
    'host': '10.1.201.58',
    'db': 'sri',
    'port': 3306,
}

REDIS_HOST = '10.1.201.16'
REDIS_PORT = 6379

MYSQL_CONFIG_ROOT = '/etc/sri/mysql'

APP_PORT = 8881
LEVI_NGINX_PORT = 80

try:
    from local_config import *
except ImportError:
    pass

DATABASE_URI = 'mysql://{user}:{passwd}@{host}/{db}'.format(**MYSQL_CONFIG)
