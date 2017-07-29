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

from ..help.helping import setupTmpBaseDir, verify64u, makeSignedAgentReg

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
    gDbEnv.open_db(b'did2offer', dupsort=True)  # table of offer expirations keyed by offer relative dids
    gDbEnv.open_db(b'track', dupsort=True)  # tracking messages
    gDbEnv.open_db(b'expire2eid', dupsort=True)  # expiration to track

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


def putSigned(key, ser, sig,  dbn="core", env=None, clobber=True):
    """
    Put signed serialization ser with signature sig at key did in named sub
    database dbn in lmdb database environment env. If clobber is False then
    raise DatabaseError exception if entry at key did is already present.

    Parameters:
        key is DID relative key str for agent data resource in database
        ser is JSON serialization of dat
        sig is signature of resource using private signing key corresponding
            to did indexed key given by signer field in dat

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

    keyb = key.encode("utf-8")
    subDb = env.open_db(dbn.encode("utf-8"))  # open named sub db named dbn within env
    with env.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        rsrcb = (ser + SEPARATOR + sig).encode("utf-8")  # keys and values must be bytes
        result = txn.put(keyb, rsrcb, overwrite=clobber )
        if not result:
            raise DatabaseError("Preexisting entry at key {}".format(key))
    return True

def putHid(hid, did, dbn="hid2did", env=None):
    """
    Put entry in HID to DID table
    assumes the each HID is unique so just overwrites
    key is hid  value is did

    Could make this better by using db .replace and checking that previous value
    is the same
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    subDb = env.open_db(dbn.encode("utf-8"))  # open named sub dbn within env
    with env.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        # will overwrite by default
        result = txn.put(hid.encode("utf-8"), did.encode("utf-8"))  # keys and values are bytes
    return result

def getSelfSigned(did, dbn='core', env=None):
    """
    Returns tuple of (dat, ser, sig) corresponding to self-signed data resource
    at did in named dbn of env.

    Raises DatabaseError exception
    IF data resource not found
    IF self-signed signature stored in resource does not verify


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
            raise DatabaseError("Resource not found.")

    rsrc = rsrcb.decode("utf-8")
    ser, sep, sig = rsrc.partition(SEPARATOR)
    try:
        dat = json.loads(ser, object_pairs_hook=ODict)
    except ValueError as ex:
        raise DatabaseError("Resource failed deserialization. {}".format(ex))

    try:
        sdid, index = dat["signer"].rsplit("#", maxsplit=1)
        index = int(index)  # get index and sdid from signer field
    except (KeyError, ValueError) as ex:
            raise DatabaseError('Invalid or missing did key index')  # missing sdid or index

    if sdid != dat['did']:
        raise DatabaseError('Invalid Self-Signer DID')

    try:
        key = dat['keys'][index]['key']
    except (TypeError, IndexError, KeyError) as ex:
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

    Raises DatabaseError exception
    If data resource not found
    If signer does not exist
    If signatures do not verify

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
            raise DatabaseError("Resource not found.")

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

    try:
        key = sdat['keys'][index]['key']
    except (IndexError, KeyError) as ex:
        raise DatabaseError('Missing verification key')

    if not verify64u(sig, ser, key):
        raise DatabaseError('Signature verification failed')

    return (dat, ser, sig)

def exists(key, dbn='core', env=None, dup=False):
    """
    Returns true if key exists in named database dbn of environment env
    False otherwise


    Parameters:
        key is key str for database
        dbn is name str of named sub database, Default is 'core'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
        dup is dupsort does the database allow duplicates
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    # read from database
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=dup)  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        rsrcb = txn.get(key.encode("utf-8"))
        if rsrcb is None:  # does not exist
            return False
    return True

def putDidOfferExpire(did, ouid, expire, dbn="did2offer", env=None):
    """
    Put entry into database table that maps offers to expiring offers expirations
    and database keys
    Database allows duplicates

    where
        did is thing DID
        ouid is offer unique id

    The key for the entry is just the did
    The value of the entry is serialized JSON
    {
        "offer": "{did}/offer/{ouid}",  # key of offer entry in core database
        "expire": "2000-01-01T00:36:00+00:00", #  ISO-8601 expiration date of offer
    }
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    offer = "{}/offer/{}".format(did, ouid)
    data = ODict()
    data["offer"] = offer
    data["expire"] = expire
    ser = json.dumps(data, indent=2)

    subDb = env.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub dbn within env
    with env.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        # if dupsort True means makes duplicates on writes to same key
        result = txn.put(did.encode("utf-8"), ser.encode("utf-8"))  # keys and values are bytes

    result = data if result else {}  # return data written or empty dict is None
    return result

def getOfferExpires(did, lastOnly=True, dbn='did2offer', env=None):
    """
    Returns list earliest to latest with offer data entriesfor given did If any
    If none exist returns empty list
    If lastOnly is True (default) then list contains only the last offer

    Each offer data is ODict
    {
        "offer": "{did}/offer/{ouid}",  # key of offer entry in core database
        "expire": "2000-01-01T00:36:00+00:00", #  ISO-8601 expiration date of offer
    }


    Parameters:
        did is thing did
        lastOnly is True then returns only the last key in list
        dbn is name str of named sub database, Default is 'did2offer'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    entries = []
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        cursor = txn.cursor()
        if cursor.set_key(did.encode("utf-8")):
            if lastOnly:
                cursor.last_dup()
                entries.append(json.loads(cursor.value().decode("utf-8"),
                                          object_pairs_hook=ODict))
            else:
                entries = [json.loads(value.decode("utf-8"), object_pairs_hook=ODict)
                           for value in cursor.iternext_dup()]

    return entries


def putTrack(key, data, dbn="track", env=None):
    """
    Put entry into database  for serialized track ser at key eid with duplicates

    Database allows duplicates

    where
        key is ephemeral ID
        data is track data

    The key for the entry is just the eid

    The value of the entry is serialized JSON
    {
        create: "2000-01-01T00:36:00+00:00", # ISO-8601 creation in server time
        expire: "2000-01-01T12:36:00+00:00", # ISO-8601 expiration in server time
        track:
        {
            eid: "abcdef01,  # lower case hex of eid
            loc: "11112222", # lower case hex of location
            dts: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of track gateway time
        }
    }
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    ser = json.dumps(data, indent=2)

    subDb = env.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub dbn within env
    with env.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        # if dupsort True means makes duplicates on writes to same key
        result = txn.put(key.encode("utf-8"), ser.encode("utf-8"))  # keys and values are bytes
        if result is None:  # error with put
            raise DatabaseError("Could not write.")


def getTracks(key, dbn='track', env=None):
    """
    Returns list earliest to latest with track entries at key eid
    If none exist returns empty list

    Each track entry is ODict
    {
        create: "2000-01-01T00:36:00+00:00", # ISO-8601 creation in server time
        expire: "2000-01-01T12:36:00+00:00", # ISO-8601 expiration in server time
        track:
        {
            eid: "abcdef01,  # lower case hex of eid
            loc: "11112222", # lower case hex of location
            dts: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of track gateway time
        }
    }


    Parameters:
        key is track eid
        dbn is name str of named sub database, Default is 'track'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    entries = []
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        cursor = txn.cursor()
        if cursor.set_key(key.encode("utf-8")):
            entries = [json.loads(value.decode("utf-8"), object_pairs_hook=ODict)
                           for value in cursor.iternext_dup()]

    return entries

def deleteTracks(key, dbn='track', env=None):
    """
    Deletes tracks at key eid

    Parameters:
        key is track eid
        dbn is name str of named sub database, Default is 'track'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        result = txn.delete(key.encode("utf-8"))
    return result


def putExpireEid(expire, eid, dbn="expire2eid", env=None):
    """
    Put entry into database table that maps expiration to track

    Database allows duplicates

    where
        expire is expiration datetime of track
        eid is track ephemeral ID

    The key for the entry is just the expiration datetime expire
    The value is just the eid

    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    subDb = env.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub dbn within env
    with env.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        # if dupsort True means makes duplicates on writes to same key
        result = txn.put(expire.encode("utf-8"), eid.encode("utf-8"))  # keys and values are bytes
        if result is None:  # error with put
            raise DatabaseError("Could not write.")

def getExpireEid(key, dbn='expire2eid', env=None):
    """
    Returns list earliest to latest with eid entries at key expire
    If none exist returns empty list

    Each entry is eid

    Parameters:
        key is expire
        dbn is name str of named sub database, Default is 'track'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    entries = []
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        cursor = txn.cursor()
        if cursor.set_key(key.encode("utf-8")):
            entries = [value for value in cursor.iternext_dup()]

    return entries
