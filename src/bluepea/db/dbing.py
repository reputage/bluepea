# -*- encoding: utf-8 -*-
"""
DBing Module

"""
from __future__ import generator_stop

import os
from collections import OrderedDict as ODict, deque
import enum

try:
    import simplejson as json
except ImportError:
    import json


import lmdb

from ioflo.aid.sixing import *
from ioflo.aid import getConsole

from ..bluepeaing import SEPARATOR, BluepeaError

from ..help.helping import setupTmpBaseDir, verify64u

console = getConsole()

MAX_DB_COUNT = 8

DATABASE_DIR_PATH = "/var/bluepea/db"  # default
ALT_DATABASE_DIR_PATH = os.path.join('~', '.indigo/bluepea/db')

gDbDirPath = None  # database directory location has not been set up yet
gDbEnv = None  # database environment has not been set up yet


class DatabaseError(BluepeaError):
    """
    Database related errors
    Usage:
        raise DBError("error message")
    """


def setupDbEnv(baseDirPath=None):
    """
    Setup  the module globals gDbEnv, gDbDirPath using baseDirPath
    if provided otherwise use DATABASE_DIR_PATH

    """
    global gDbEnv, gDbDirPath

    if not baseDirPath:
        baseDirPath = DATABASE_DIR_PATH

    baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
    if not os.path.exists(baseDirPath):
        try:
            os.makedirs(baseDirPath)
        except OSError as ex:
            baseDirPath = ALT_DATABASE_DIR_PATH
            baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
            if not os.path.exists(baseDirPath):
                os.makedirs(baseDirPath)
    else:
        if not os.access(baseDirPath, os.R_OK | os.W_OK):
            baseDirPath = ALT_DATABASE_DIR_PATH
            baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
            if not os.path.exists(baseDirPath):
                os.makedirs(baseDirPath)

    gDbDirPath = baseDirPath  # set global

    gDbEnv = lmdb.open(gDbDirPath, max_dbs=MAX_DB_COUNT)
    # creates files data.mdb and lock.mdb in dbBaseDirPath

    # create named dbs  (core and tables)
    gDbEnv.open_db(b'core')
    gDbEnv.open_db(b'hid2did')  # table of dids keyed by hids

    # verify that the server resource is present in the database
    # need to read in saved server signing keys and query database
    # if not present then create server resource

    return gDbEnv

def setupTestDbEnv():
    """
    Return dbEnv resulting from baseDirpath in temporary directory
    and then setupDbEnv
    """
    baseDirPath = setupTmpBaseDir()
    baseDirPath = os.path.join(baseDirPath, "db/bluepea")
    os.makedirs(baseDirPath)
    return setupDbEnv(baseDirPath=baseDirPath)


def createServerResource(vk, sk, changed=None,  **kwa):
    """
    Create and add Server resource to database given verifier key vk and
    signing key sk
    changed is optional dattime stamp if not provided use current datetime

    Assumes that global keeper and dbEnv are already setup
    """


def putSigned(ser, sig, did, dbn='core', env=None, clobber=True):
    """
    Put signed serialization ser with signature sig at key did in named sub
    database dbn in lmdb database environment env. If clobber is False then
    raise DatabaseError exception if entry at key did is already present.

    Parameters:
        ser is JSON serialization of dat
        sig is signature of resource using private signing key corresponding
            to did indexed key given by signer field in dat
        did is DID str for agent data resource in database
        dbn is name str of named sub database, Default is 'core'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
        clobber is Boolean If False then raise error if entry at did already
            exists in database
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    didb = did.encode("utf-8")
    subDb = gDbEnv.open_db(dbn.encode("utf-8"))  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        rsrcb = txn.get(didb)
        if clobber and rsrcb is not None:  # pre-existing
            raise DatabaseError("Preexisting entry at DID")
        rsrc = ser + SEPARATOR + sig
        txn.put(didb, rsrc.encode("utf-8") )  # keys and values are bytes


def getSelfSigned(did, dbn='core', env=None):
    """
    Returns tuple of (dat, ser, sig) corresponding to self-signed data resource
    at did in named dbn of env.
    Returns tuple (None, None, None) if data resource not found
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
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    # read from database
    subDb = gDbEnv.open_db(dbn.encode("utf-8"))  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        rsrcb = txn.get(did.encode("utf-8"))
        if rsrcb is None:  # does not exist
            return (None, None, None)

    rsrc = rsrcb.decode("utf-8")
    ser, sep, sig = rsrc.partition(SEPARATOR)
    try:
        dat = json.loads(ser, object_pairs_hook=ODict)
    except ValueError as ex:
        raise DatabaseError("Resource failed deserialization. {}".format(ex))

    try:
        sdid, index = dat["signer"].rsplit("#", maxsplit=1)
        index = int(index)  # get index and sdid from signer field
    except (AttributeError, ValueError) as ex:
            raise DatabaseError('Invalid or missing did key index')  # missing sdid or index

    if sdid != dat['did']:
        raise DatabaseError('Invalid Self-Signer DID')

    try:
        key = dat['keys'][index]['key']
    except (IndexError, KeyError) as ex:
        raise DatabaseError('Missing verification key')

    if not verify64u(sig, ser, key):
        raise DatabaseError('Self signature verification failed')

    return (dat, ser, sig)


def getSigned(did, dbn='core', env=None):
    """
    Returns tuple of (dat, ser, sig) corresponding to Non-self-signed data resource
    at did in named dbn of env.
    Looks up and verifies signer's data resource and then verfies data resource
    given verification key provided by signer's data resource.

    Returns tuple (None, None, None) if data resource not found
    If signatures do not verify then raises DatabaseError exception
    If signer does not exist then raises DatabaseError exception

    In return tuple:
        dat is ODict JSON deserialization of ser
        ser is JSON serialization of dat
        sig is signature of resource using private signing key corresponding
            to signer's did indexed key given by signer field in dat


    Parameters:
        did is DID str for agent data resource in database
        dbn is name str of named sub database, Default is 'core'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    # read from database
    subDb = gDbEnv.open_db(dbn.encode("utf-8"))  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        rsrcb = txn.get(did.encode("utf-8"))
        if rsrcb is None:  # does not exist
            return (None, None, None)

    rsrc = rsrcb.decode("utf-8")
    ser, sep, sig = rsrc.partition(SEPARATOR)
    try:
        dat = json.loads(ser, object_pairs_hook=ODict)
    except ValueError as ex:
        raise DatabaseError("Resource failed deserialization. {}".format(ex))

    try:
        sdid, index = dat["signer"].rsplit("#", maxsplit=1)
        index = int(index)  # get index and sdid from signer field
    except (AttributeError, ValueError) as ex:
            raise DatabaseError('Invalid or missing did key index')  # missing sdid or index

    try:
        sdat, sser, ssig = getSelfSigned(sdid)
    except DatabaseError as ex:
        raise DatabaseError("Signer errored as {}".format(ex.args[0]))

    if sdat is None:
        raise DatabaseError("Signer not found")

    try:
        key = sdat['keys'][index]['key']
    except (IndexError, KeyError) as ex:
        raise DatabaseError('Missing verification key')

    if not verify64u(sig, ser, key):
        raise DatabaseError('Signature verification failed')

    return (dat, ser, sig)

