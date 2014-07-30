# coding: utf-8

DEV = False
MYSQL_CONFIG = {
    'user': 'platform_root',
    'passwd': 'mnjksghqFGeksh342ui',
    'host': '10.1.201.58',
    'db': 'sri',
}
DATABASE_URI = 'mysql://{user}:{passwd}@{host}/{db}'.format(**MYSQL_CONFIG)

REDIS_HOST = '10.1.201.16'
REDIS_PORT = 6379

MYSQL_CONFIG_ROOT = '/etc/sri/mysql'

try:
    from local_config import *
except ImportError:
    pass
