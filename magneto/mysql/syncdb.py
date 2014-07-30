# coding:utf-8

import logging
from collections import OrderedDict

from magneto.mysql import sentinel

CREATE_TABLE_SQL = r'''
                        CREATE TABLE `%s` (
                            %s
                            %s
                        ) %s
                    '''
DROP_DATABASE_SQL = r'''DROP DATABASE `%s`;'''
CREATE_DATABASE_SQL = r'''CREATE DATABASE `%s`;'''
ALTER_TABLE_SQL = r'''ALTER TABLE `%s` ADD `%s` %s;'''
ALTER_ADDITION_SQL = r'''ALTER TABLE `%s` ADD %s;'''
SHOW_STATUS_SQL = r'''SHOW TABLE STATUS WHERE NAME = '%s';'''
INSERT_DATA_SQL = r'''INSERT INTO `{0}` VALUES({1});'''
SET_NAMES_SQL = r'''SET NAMES UTF8;'''

logger = logging.getLogger()

class SyncDbException(Exception):
    def __init__(self, msg):
        super(SyncDbException, self).__init__(msg)
        self._msg = '%s, Plz Contact DBA For Help' % msg

    def __str__(self):
        return self._msg

def syncdb(data):
    appname = data['application']
    local, table_additions = loads(data['local'])
    local_data = data['data']
    reset = data['reset']

    conn = connect(appname)
    if reset:
        reset_db(conn, appname)

    remote = dumps(conn)
    sync_tables(conn, local, remote, table_additions)

    remote = dumps(conn)
    sync_columns(conn, local, remote)

    if local_data:
        sync_data(conn, local_data)

    remote = dumps(conn)
    sync_additions(conn, local, remote)

def reset_db(conn, appname):
    cur = conn.cursor()
    try:
        cur.execute(DROP_DATABASE_SQL % appname)
        cur.execute(CREATE_DATABASE_SQL % appname)
        conn.select_db(appname)
    except Exception:
        logger.exception('reset error occured.')
    cur.close()
    return True

def sync_tables(conn, local, remote, table_additions):
    cur = conn.cursor()
    #local指app的本地数据库，remote指远端数据库
    local_tables = set(local)
    remote_tables = set(remote)
    if not remote_exists(local_tables, remote_tables):
        raise SyncDbException('Append Table Only')

    for table in local_tables.difference(remote_tables):
        cols = []
        additions = ['%s,' % addition for addition in local[table][:-1] if not addition.startswith('CONSTRAINT')]
        for column, define in local[table][-1].iteritems():
            cols.append('`%s` %s,' % (column, define))
        #delete last comma, it cause sql exception
        if additions:
            additions[-1] = additions[-1][:-1]
        else:
            cols[-1] = cols[-1][:-1]
        sql = ''
        try:
            sql = CREATE_TABLE_SQL % (table, '\n'.join(cols), '\n'.join(additions), \
                    ' '.join(table_additions[table]))
            cur.execute(sql)
        except Exception:
            logger.exception('Sync table error occured.')
        finally:
            logger.debug(sql)

    cur.close()
    return True

def sync_columns(conn, local, remote):
    cur = conn.cursor()
    #local指app的本地数据库，remote指远端数据库
    local_tables = set(local.keys())
    remote_tables = set(remote.keys())

    for table in remote_tables.intersection(local_tables):
        #最后一行为结构
        local_struct = local[table][-1]
        remote_struct = remote[table][-1]
        if not remote_exists(local_struct, remote_struct):
            raise SyncDbException('Append Column Only')

        for column, define in local_struct.iteritems():
            if remote_struct.has_key(column) and not cmp(define.upper(), remote_struct[column].upper()):
                continue
            if remote_struct.has_key(column) and \
                    (cmp(define.upper(), remote_struct[column].upper()) or \
                    define.upper() in remote_struct[column].upper()):
                logger.info('table %s column %s can\'t sync. define %s, remote %s' \
                        % (table, column, define, remote_struct[column]))
                raise SyncDbException('Can not Change Column')
            if not remote_struct.has_key(column):
                sql = ''
                try:
                    sql = ALTER_TABLE_SQL % (table, column, define)
                    cur.execute(sql)
                except Exception:
                    logger.exception('Syncdb column error occured.')
                finally:
                    logger.debug(sql)

    cur.close()
    return True

def sync_additions(conn, local, remote, limit = 7036874417766399):
    cur = conn.cursor()

    for table, define in local.iteritems():
        local_addition = define[:-1]
        remote_addition = []

        if remote.has_key(table):
            remote_addition = remote[table][:-1]
        else: continue

        if not remote_exists(local_addition, remote_addition):
            logger.info('table %s can\'t sync. define %s, remote %s' \
                    % (table, local_addition, remote_addition))
            raise SyncDbException('Append Index Only')
        if is_big_table(cur, table, limit):
            raise SyncDbException('Table %s is Big' % table) 

        for addition in set(local_addition).difference(set(remote_addition)):
            sql = ''
            try:
                sql = ALTER_ADDITION_SQL % (table, addition)
                cur.execute(sql)
            except Exception:
                logger.exception('Add additions error occured.')
            finally:
                logger.debug(sql)

    cur.close()
    return True

def sync_data(conn, data):
    cur = conn.cursor()
    cur.execute(SET_NAMES_SQL)
    for table, datas in data.iteritems():
        if not datas:
            continue
        logger.debug(table)
        for data in datas:
            sql = ''
            try:
                sql = INSERT_DATA_SQL.format(table, ','.join(["%s"] * len(data)))
                cur.execute(sql, [col.encode('utf8') if isinstance(col, unicode) else col for col in data])
                conn.commit()
            except Exception,e:
                logger.exception('Sync data error occured. %s' % str(e))
                conn.rollback()
            finally:
                logger.debug(data)

    cur.close()
    return True

def remote_exists(local, remote):
    local = set(local)
    remote = set(remote)
    return remote.issubset(local)

def is_big_table(cur, table, limit):
    ret = False
    sql = ''
    try:
        sql = SHOW_STATUS_SQL % table
        cur.execute(sql)
        #6 is Data_length
        ret = int(cur.fetchall()[0][6])
        ret = ret > limit
    except Exception:
        logger.exception('Check table error occured.')
    finally:
        logger.debug(sql)
        return ret

def dumps(conn):
    cur = conn.cursor()
    cur.execute(r'SHOW TABLES;')
    tables = cur.fetchall()
    result = OrderedDict()
    for table in tables:
        cur.execute(r'SHOW CREATE TABLE `%s`;' % table[0])
        struct = OrderedDict()
        result[table[0]] = []
        ret_list = cur.fetchall()[0][1].split('\n')
        for col in ret_list[1:-1]:
            col = col.strip()
            if not col[0] == '`':
                result[table[0]].append(col.strip(','))
                continue
            struct.update(split_sql(col))
        result[table[0]].append(struct)
    cur.close()
    return result

def loads(dumps):
    result = OrderedDict()
    table_additions = {}
    for table in dumps:
        table_name = table.keys()[0]
        table_additions[table_name] = table[table_name].pop()
        table_columns = table[table_name].pop()
        result[table_name] = table[table_name]
        struct = OrderedDict()
        for column in table_columns:
            for column_name, column_define in column.iteritems():
                struct[column_name] = column_define
        result[table_name].append(struct)
    return result, table_additions

def split_sql(col):
    col_name = col[1:col.find('`', 1)]
    if col.endswith(','):
        col_struct = col[col.find('`', 1) + 1:col.rfind(',')].strip()
    else:
        col_struct = col[col.find('`', 1) + 1:].strip()
    return {col_name: col_struct}

def connect(appname):
    return sentinel.select_database(appname)
