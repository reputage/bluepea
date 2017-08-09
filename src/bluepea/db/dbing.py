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
import arrow

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
        raise DatabaseError("error message")
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
    gDbEnv.open_db(b'anon', dupsort=True)  # anonymous messages
    gDbEnv.open_db(b'expire2eid', dupsort=True)  # expiration to eid anon

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
        with txn.cursor() as cursor:
            if cursor.set_key(did.encode("utf-8")):
                if lastOnly:
                    cursor.last_dup()
                    entries.append(json.loads(cursor.value().decode("utf-8"),
                                              object_pairs_hook=ODict))
                else:
                    entries = [json.loads(value.decode("utf-8"), object_pairs_hook=ODict)
                               for value in cursor.iternext_dup()]

    return entries


def putTrack(key, data, dbn="anon", env=None):
    """
    Put entry into database  for serialized anon message ser at key eid with duplicates

    Database allows duplicates

    where
        key is ephemeral ID
        data is anon msg data

    The key for the entry is just the eid

    The value of the entry is serialized JSON

    eid is track ephemeral ID in base64 url safe  up to 16 bytes
    msg is location string in base 64 url safe up to 144 bytes
    dts is iso8601 datetime stamp

    The value of the entry is serialized JSON
    {
        create: 1501774813367861, # creation in server time microseconds since epoch
        expire: 1501818013367861, # expiration in server time microseconds since epoch
        track:
        {
            eid: "AQIDBAoLDA0=",  # base64 url safe of 8 byte eid
            msg: "EjRWeBI0Vng=", # base64 url safe of 8 byte location
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
        result = txn.put(key.encode(), ser.encode())  # keys and values are bytes
        if result is None:  # error with put
            raise DatabaseError("Could not write.")
        return result


def getTracks(key, dbn='anon', env=None):
    """
    Returns list earliest to latest with anon entries at key eid
    If none exist returns empty list

    Each anon entry is ODict

    eid is anon ephemeral ID in base64 url safe  up to 16 bytes
    msg is location string in base 64 url safe up to 144 bytes
    dts is iso8601 datetime stamp

    The value of the entry is serialized JSON
    {
        create: 1501774813367861, # creation in server time microseconds since epoch
        expire: 1501818013367861, # expiration in server time microseconds since epoch
        track:
        {
            eid: "AQIDBAoLDA0=",  # base64 url safe of 8 byte eid
            msg: "EjRWeBI0Vng=", # base64 url safe of 8 byte location
            dts: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of track gateway time
        }
    }

    Parameters:
        key is track eid
        dbn is name str of named sub database, Default is 'anon'
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
        with txn.cursor() as cursor:
            if cursor.set_key(key.encode("utf-8")):
                entries = [json.loads(value.decode("utf-8"), object_pairs_hook=ODict)
                               for value in cursor.iternext_dup()]
    return entries

def deleteTracks(key, dbn='anon', env=None):
    """
    Deletes tracks at key eid

    Parameters:
        key is track eid
        dbn is name str of named sub database, Default is 'anon'
        env is main LMDB database environment
            If env is not provided then use global gDbEnv
    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)  # open named sub db named dbn within env
    with gDbEnv.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        result = txn.delete(key.encode("utf-8"))
        if result is None:  # error with put
            raise DatabaseError("Could not delete.")
    return result


def putExpireEid(key, eid, dbn="expire2eid", env=None):
    """
    Put entry into database table that maps expiration to anon

    Database allows duplicates

    where
        key is expiration datetime of anon int
        eid is anon ephemeral ID

    The key for the entry is just the expiration datetime expire
    The value is just the eid

    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    keyb = key.to_bytes(8, "big")
    # open named sub dbn within env
    subDb = env.open_db(dbn.encode("utf-8"), dupsort=True)
    with env.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        # if dupsort True means makes duplicates on writes to same key
        result = txn.put(keyb, eid.encode("utf-8"))  # keys and values are bytes
        if result is None:  # error with put
            raise DatabaseError("Could not write.")
        return result

def getExpireEid(key, dbn='expire2eid', env=None):
    """
    Returns list earliest to latest with eid entries at key expire
    If none exist returns empty list

    Each entry is eid

    Parameters:
        key is expire int

    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    entries = []
    keyb = key.to_bytes(8, "big")
    # open named sub db named dbn within env
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)
    with gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        with txn.cursor() as cursor:
            if cursor.set_key(keyb):
                entries = [value.decode("utf-8") for value in cursor.iternext_dup()]
    return entries

def deleteExpireEid(key, dbn='expire2eid', env=None):
    """
    Deletes expire eid entries

    Parameters:
        key is expire date

    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    keyb = key.to_bytes(8, "big")
    # open named sub db named dbn within env
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)
    with gDbEnv.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        result = txn.delete(keyb)
    return result

def popExpired(key, dbn='expire2eid', env=None):
    """
    Returns list of expired eids and then deletes them for earliest entry
    in database that is less than or equal to key if any
    Otherwise returns empty list

    Call iteratively to get all the earlier entries in the database

    Parameters:
        key is expire timestamp in int microseconds since epoch

    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    entries = []
    expire = key
    keyb = key.to_bytes(8, "big")
    # open named sub db named dbn within env
    subDb = gDbEnv.open_db(dbn.encode("utf-8"), dupsort=True)
    with gDbEnv.begin(db=subDb, write=True) as txn:  # txn is a Transaction object
        with txn.cursor() as cursor:
            if cursor.first():
                curb = cursor.key()
                current = int.from_bytes(curb, "big")
                if current <= expire:  # current entry is expired
                    entries = [value.decode("utf-8") for value in cursor.iternext_dup()]
                    if entries:
                        if not cursor.key():
                            if not cursor.first_dup():  # iterator makes key() be blank so reset
                                raise DatabaseError("Problem setting cursor to entry")
                            if not cursor.delete(dupdata=True):  # delete all dups
                                raise DatabaseError("Problem deleting entry")
    return entries


def clearStaleTracks(key, tdbn='anon', edbn='expire2eid', env=None):
    """
    Clears expired tracks at or earlier to timestamp key
    and their entries in the anon and expire2eid databases

    Returns True if successfully cleared at least one stale anon

    Parameters:
        key is expire timestamp in microseconds since epoch

    """
    global gDbEnv

    if env is None:
        env = gDbEnv

    if env is None:
        raise DatabaseError("Database environment not set up")

    success = False
    while True:
        entries = popExpired(key=key, dbn=edbn, env=env)
        if not entries:
            break

        for entry in entries:
            result = deleteTracks(key=entry, dbn=tdbn, env=env)
            if result:
                success = True
    return success
