#!/usr/bin/env python
#coding:utf-8

import hashlib
import MySQLdb

from magneto.config import MYSQL_CONFIG


class MySQLSentinel(object):

    def __init__(self):
        conf = MYSQL_CONFIG.copy()
        conf.setdefault('use_unicode', False)
        conf.setdefault('charset', 'utf8')

        self._conn = MySQLdb.connect(**conf)

    def select_database(self, appname):
        '''
            use for syncdb,
            need database named dae_appname,
            if not exists will create first.
        '''
        db = appname

        if not getattr(self._conn, 'select_db', None):
            def select_db(db):
                try:
                    self._conn.db = db
                    self._conn.query("USE %s" % db)
                except MySQLdb.InternalError as e:
                    if e[0] == 1049:
                        raise MySQLdb.OperationalError
                    raise
            setattr(self._conn, 'select_db', select_db)

        try:
            self._conn.select_db(db)
        except (MySQLdb.OperationalError, MySQLdb.InternalError):
            self.create_database(db)
            self._conn.select_db(db)
        return self._conn

    def create_database(self, db):
        sql_cmd = 'CREATE DATABASE IF NOT EXISTS `%s`;'
        self._execute(sql_cmd % db)

    def grant_database(self, appname, passwd, manager_passwd):
        self.select_database(appname)
        sql = ("grant drop, create, select, insert, update, delete "
                "on `%s`.* to '%s'@'%%' identified by '%s'")
        self._execute(sql % (appname, appname, passwd))
        # grant manager
        manager = hashlib.sha256(appname).hexdigest()[:16]
        sql = ("grant alter, drop, create, select, insert, update, delete "
                "on `%s`.* to '%s'@'%%' identified by '%s'")
        self._execute(sql % (appname, manager, manager_passwd))

    def _execute(self, sql_cmd, para=()):
        cur = self._conn.cursor()
        cur.execute(sql_cmd)
        self._conn.commit()
        cur.close()

    @property
    def connection(self):
        return self._conn


sentinel = MySQLSentinel()


def setup_mysql(appname, password, manager_password):
    sentinel.create_database(appname)
    sentinel.grant_database(appname, password, manager_password)


def list_slow_user():
    sentinel.select_database('information_schema')
    cur = sentinel.connection.cursor()
    cur.execute("SELECT user, sum(time) AS _time FROM processlist "
                "WHERE command = 'query' GROUP BY user HAVING _time > 60")
    for user, time in cur:
        print '%s,%s' % (user, time)
