# -*- encoding: utf-8 -*-
"""
Priming Module

Prepares or primes setup of environment

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

from ..help.helping import setupTmpBaseDir

from ..db import dbing
from ..keep import keeping

console = getConsole()

def setup(keepDirPath=None, seed=None, prikey=None, dbDirPath=None, changed=None):
    keeper = keeping.setupKeeper(baseDirPath=keepDirPath, seed=seed, prikey=prikey)
    dbEnv = dbing.setupDbEnv(baseDirPath=dbDirPath)
    createServerResource(vk=keeper.verkey,
                         sk=keeper.sigkey,
                         changed=changed)

def setupTest():
    seed = (b'\x0c\xaa\xc9\xc6G\x11\xf6nn\xd7\x1b7\xdc^i\xc5\x12O\xe9>\xe1$F\xe1'
            b'\xa4z\xd4\xb6P\xdd\x86\x1d')

    prikey = (b'\xd9\xc8<$\x03\xb9%\x03c\xb3*6g\xa7m\xd8\x8d\x08j\xd4^4\x88\xcac\xba\xd1\xe9'
              b'\xd9\xe6\x99%')

    baseDirPath = setupTmpBaseDir()
    keepDirPath = os.path.join(baseDirPath, "bluepea/keep")
    os.makedirs(keepDirPath)
    dbDirPath = os.path.join(baseDirPath, "bluepea/db")
    os.makedirs(dbDirPath)

    setup(keepDirPath=keepDirPath, seed=seed, prikey=prikey, dbDirPath=dbDirPath)


def createServerResource(vk, sk, changed=None,  **kwa):
    """
    Create and add Server resource to database if not already present
    given verifier key vk and
    signing key sk
    changed is optional dattime stamp if not provided use current datetime

    Assumes that global keeper and dbEnv are already setup
    """
    keeper = keeping.gKeeper
    did = keeper.did
    dat, ser, sig = dbing.getSelfSigned(did)  # see if valid already exists
    if dat is None:  # need to create
        sig, ser = dbing.makeSignedAgentReg(vk=keeper.verkey,
                                      sk=keeper.sigkey,
                                      changed=changed)
        dbing.putSigned(ser, sig, did)  # clobber in case was corrupted to fix



