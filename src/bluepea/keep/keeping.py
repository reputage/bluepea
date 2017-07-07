# -*- encoding: utf-8 -*-
"""
Keeping Module

"""
from __future__ import generator_stop

import os
import stat
import shutil
from collections import OrderedDict as ODict, deque
import enum

try:
    import simplejson as json
except ImportError:
    import json

try:
    import msgpack
except ImportError:
    pass


from ioflo.aid.sixing import *
from ioflo.aid import filing
from ioflo.aid import getConsole

from ..help.helping import setupTmpBaseDir

console = getConsole()

KEEP_DIR_PATH = "/var/keep/bluepea"  # default
ALT_KEEP_DIR_PATH = os.path.join('~', '.indigo/keep/bluepea')

KeepDirPath = None  # key directory location has not been set up yet


def setupKeep(baseDirPath=None):
    """
    Setup  the module global KeepDirPath using baseDirPath
    if provided otherwise use KEEP_DIR_PATH

    """
    global KeepDirPath

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

    KeepDirPath = baseDirPath  # set global

    # restore keys if any

    # keys = loadAllKeys(KeepDirPath)


    return KeepDirPath

def setupTestKeep():
    """
    Return KeepDirPath resulting from baseDirpath in temporary directory
    and then setupKeep
    """
    baseDirPath = setupTmpBaseDir()
    baseDirPath = os.path.join(baseDirPath, "keep/bluepea")
    os.makedirs(baseDirPath)
    return setupKeep(baseDirPath=baseDirPath)

def dumpKeys(data, filepath):
    '''
    Write data as as type self.ext to filepath. json or msgpack
    '''
    if ' ' in filepath:
        raise IOError("Invalid filepath '{0}' "
                                "contains space".format(filepath))

    perm_other = stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
    perm_group = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
    cumask = os.umask(perm_other | perm_group)  # save old into cumask and set new

    root, ext = os.path.splitext(filepath)
    if ext == '.json':
        with filing.ocfn(filepath, "w+") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.msgpack':
        if not msgpack:
            raise IOError("Invalid filepath ext '{0}' "
                        "needs msgpack installed".format(filepath))
        with filing.ocfn(filepath, "w+b", binary=True) as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError("Invalid filepath ext '{0}' "
                    "not '.json' or '.msgpack'".format(filepath))

    os.umask(cumask)  # restore old


def loadKeys(filepath):
    '''
    Return data read from filepath as converted json
    Otherwise return None
    '''
    try:
        root, ext = os.path.splitext(filepath)
        if ext == '.json':
            with filing.ocfn(filepath, "r") as f:
                it = json.load(f, object_pairs_hook=ODict)
        elif ext == '.msgpack':
            if not msgpack:
                raise IOError("Invalid filepath ext '{0}' "
                            "needs msgpack installed".format(filepath))
            with filing.ocfn(filepath, "rb", binary=True) as f:
                it = msgpack.load(f, object_pairs_hook=ODict)
        else:
            it = None
    except EOFError:
        return None
    except ValueError:
        return None
    return it

def loadAllKeyRoles(dirpath, prefix="key", role=""):
    """
    Load and Return the keys dict indexed by role for all key data files with
    prefix in  directory at dirpath  both .json and .msgpack file extensions
    are supported

    If role is not empty then loads last keyfile that matches both prefix and role

    key files names of form:
    prefix.role.json
    prefix.role.msgpack

    (when prefix is the default "key" )
    key.server.json
    key.server.msgpack

    key fields in keyfiles should be in:
    ('seed', 'sigkey', 'verkey', 'prikey', 'pubkey')

    values are bytes of binary key value

    """
    roles = ODict()
    for filename in os.listdir(dirpath):  # filenames without directory
        filepath = os.path.join(dirpath, filename)  # need full path for isfile
        if not os.path.isfile(filepath):
            continue
        root, ext = os.path.splitext(filename)
        if ext not in ['.json', '.msgpack']:
            continue
        pre, sep, rol = root.partition('.')
        if not rol or pre != prefix or (role and rol != role):
            continue
        roles[rol] = loadKeys(filepath)
    return roles

