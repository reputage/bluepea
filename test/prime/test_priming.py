from __future__ import generator_stop

import os
import stat
import tempfile
import shutil
import binascii
import base64
import datetime

from collections import OrderedDict as ODict
try:
    import simplejson as json
except ImportError:
    import json

import libnacl

from ioflo.aid import timing

import pytest
from pytest import approx


from bluepea.help.helping import setupTmpBaseDir, cleanupTmpBaseDir

from bluepea.prime import priming
from bluepea.keep import keeping
from bluepea.db import dbing

def test_setupPrime():
    """
    Test prime setup
    """
    print("Testing setup")

    baseDirPath = setupTmpBaseDir()

    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    keepDirPath = os.path.join(baseDirPath, "bluepea/keep")
    os.makedirs(keepDirPath)
    assert os.path.exists(keepDirPath)

    seed = (b'\x0c\xaa\xc9\xc6G\x11\xf6nn\xd7\x1b7\xdc^i\xc5\x12O\xe9>\xe1$F\xe1'
            b'\xa4z\xd4\xb6P\xdd\x86\x1d')

    prikey = (b'\xd9\xc8<$\x03\xb9%\x03c\xb3*6g\xa7m\xd8\x8d\x08j\xd4^4\x88\xcac\xba\xd1\xe9'
              b'\xd9\xe6\x99%')


    dbDirPath = os.path.join(baseDirPath, "bluepea/db")
    os.makedirs(dbDirPath)
    assert os.path.exists(dbDirPath)

    priming.setup(keepDirPath=keepDirPath, seed=seed, prikey=prikey,
                  dbDirPath=dbDirPath,
                  changed=None)

    assert keeping.gKeepDirPath == keepDirPath
    assert dbing.gDbDirPath == dbDirPath

    keeper = keeping.gKeeper

    dat, ser, sig = dbing.getSelfSigned(keeper.did)
    assert dat
    assert dat['did'] == keeper.did

    cleanupTmpBaseDir(baseDirPath)
    assert not os.path.exists(baseDirPath)
    print("Done Test")

def test_setupTestPrime():
    """
    Test prime test setup
    """
    print("Testing setupTest")

    priming.setupTest()
    assert os.path.exists(keeping.gKeepDirPath)
    assert os.path.exists(dbing.gDbDirPath)

    cleanupTmpBaseDir(dbing.gDbDirPath)
    assert not os.path.exists(dbing.gDbDirPath)
    assert not os.path.exists(keeping.gKeepDirPath)
    print("Done Test")

