# coding: utf-8

DEV = False
mysql_config = {
    'user': 'platform_root',
    'passwd': 'mghqFGeksh342ui',
    'host': '10.1.201.58',
    'database': 'sri',
}
database_uri = 'mysql://{user}:{passwd}@{host}/{database}'.format(**mysql_config)

redis_host = '10.1.201.16'
redis_port = 6379

try:
    from local_config import *
except ImportError:
    pass
