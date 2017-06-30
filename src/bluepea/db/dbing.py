# -*- encoding: utf-8 -*-
"""
DBing Module

"""
from __future__ import generator_stop

import os
from collections import OrderedDict as ODict, deque
import enum

import lmdb

from ioflo.aid.sixing import *
from ioflo.aid import getConsole

console = getConsole()

MAX_DB_COUNT = 8

BASE_DIR_PATH = "/var/db/bluepea"  # default
ALT_BASE_DIR_PATH = os.path.join('~', '.bluepea')

dbBaseDirPath = None  # database directory location has not been set up yet
dbEnv = None  # database environment has not been set up yet

def setupDbEnv(baseDirPath=None):
    """
    Setup  the module globals dbBaseDirPath, dbBaseFilePath, dbEnv using baseDirPath
    if provided otherwise use BASE_DIR_PATH

    """
    global dbBaseDirPath, dbBaseFilePath, dbEnv

    if not baseDirPath:
        baseDirPath = BASE_DIR_PATH

    baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
    if not os.path.exists(baseDirPath):
        try:
            os.makedirs(baseDirPath)
        except OSError as ex:
            baseDirPath = ALT_BASE_DIR_PATH
            baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
            if not os.path.exists(baseDirPath):
                os.makedirs(baseDirPath)
    else:
        if not os.access(baseDirPath, os.R_OK | os.W_OK):
            baseDirPath = ALT_BASE_DIR_PATH
            baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
            if not os.path.exists(baseDirPath):
                os.makedirs(baseDirPath)

    dbBaseDirPath = baseDirPath  # set global

    #dbBaseFilePath = os.path.join(dbBaseDirPath, "bluepea.lmdb")  # set global

    dbEnv = lmdb.open(dbBaseDirPath, max_dbs=MAX_DB_COUNT)
    # creates files data.mdb and lock.mdb in dbBaseDirPath

    # create named dbs  (core and tables)
    dbEnv.open_db(b'core')

    return dbEnv

#with env.begin(write=True) as txn:
   #txn.put('somename', 'somedata')

if __name__ == '__main__':
    env = setupDbEnv()
    print("Setup dbEnv")
