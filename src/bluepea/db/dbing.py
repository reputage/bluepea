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

from ..help.helping import setupTmpBaseDir

console = getConsole()

MAX_DB_COUNT = 8

BASE_DIR_PATH = "/var/db/bluepea"  # default
ALT_BASE_DIR_PATH = os.path.join('~', '.bluepea')

dbDirPath = None  # database directory location has not been set up yet
dbEnv = None  # database environment has not been set up yet

def setupDbEnv(baseDirPath=None):
    """
    Setup  the module globals dbEnv, dbDirPath using baseDirPath
    if provided otherwise use BASE_DIR_PATH

    """
    global dbEnv, dbDirPath

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

    dbDirPath = baseDirPath  # set global

    dbEnv = lmdb.open(dbDirPath, max_dbs=MAX_DB_COUNT)
    # creates files data.mdb and lock.mdb in dbBaseDirPath

    # create named dbs  (core and tables)
    dbEnv.open_db(b'core')

    # verify that the server resource is present in the database
    # need to read in saved server signing keys and query database
    # if not present then create server resource

    return dbEnv

def setupTestDbEnv():
    """
    Return dbEnv resulting from baseDirpath in temporary directory
    and then setupDbEnv
    """
    baseDirPath = setupTmpBaseDir()
    baseDirPath = os.path.join(baseDirPath, "db/bluepea")
    os.makedirs(baseDirPath)
    return setupDbEnv(baseDirPath=baseDirPath)

if __name__ == '__main__':
    env = setupDbEnv()
    print("Setup dbEnv")
