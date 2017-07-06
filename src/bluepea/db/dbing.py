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

from ..bluepeaing import SEPARATOR, BluepeaError

from ..help.helping import setupTmpBaseDir

console = getConsole()

MAX_DB_COUNT = 8

BASE_DIR_PATH = "/var/db/bluepea"  # default
ALT_BASE_DIR_PATH = os.path.join('~', '.bluepea')

dbDirPath = None  # database directory location has not been set up yet
dbEnv = None  # database environment has not been set up yet

class DatabaseError(BluepeaError):
    """
    Database related errors
    Usage:
        raise DBError("error message")
    """


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
    dbEnv.open_db(b'hid2did')  # table of dids keyed by hids

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

def fetchAgentData(did, dbn='core', env=None):
    """
    Returns tuple of (dat, ser, sig) corresponding to data resource
    at did in named dbn of env.
    If self-signed signature stored in resource does not verify then
    raises DatabaseError exception

    In return tuple:
        dat is ODict JSON deserialization of ser
        ser is JSON serialization of dat
        sig is signature of resource using private signing key corresponding
            to did indexed key given by signer field in dat

    Agents data resources are self signing

    Parameters:
        did is DID str for agent data resource in database
        dbn is name str of named sub database, Default is 'core'
        env is main LMDB database environment
            If env is not provided then use global dbEnv
    """
    global dbEnv

    if env is None:
        env = dbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    # read from database
    subDb = dbEnv.open_db(dbn.encode("utf-8"))  # open named sub db named dbn within env
    with dbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        rsrcb = txn.get(did.encode("utf-8"))
        if rsrcb is None:  # does not exist
            raise DatabaseError("Missing entry at DID")

    rsrc = rsrcb.decode("utf-8")
    ser, sep, sig = rsrc.partition(SEPARATOR)
    try:
        agentRsrc = json.loads(agent, object_pairs_hook=ODict)
    except ValueError as ex:
        raise falcon.HTTPError(falcon.HTTP_424,
                                   'Data Resource Error',
                                   'Could not decode associated data resource')

    try:
        adid, aindex = agentRsrc["signer"].rsplit("#", maxsplit=1)
        aindex = int(aindex)  # get index and sdid from signer field
    except (AttributeError, ValueError) as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                               'Validation Error',
                                'Invalid or missing did key index.')   # missing sdid or index

    if adid != agentRsrc['did']:
        raise falcon.HTTPError(falcon.HTTP_424,
                               'Data Resource Error',
                               'Signing did mismatch')

    try:
        akey = agentRsrc['keys'][aindex]['key']
    except (IndexError, KeyError) as ex:
        raise falcon.HTTPError(falcon.HTTP_424,
                                       'Data Resource Error',
                                       'Missing signing key')

    if not verify64u(asig, agent, akey):
        raise falcon.HTTPError(falcon.HTTP_424,
                                       'Data Resource Error',
                                       'Invalid signing key')

if __name__ == '__main__':
    env = setupDbEnv()
    print("Setup dbEnv")
