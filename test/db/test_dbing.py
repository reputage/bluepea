from __future__ import generator_stop

import os
import stat
import tempfile
import shutil
import binascii
import base64

from collections import OrderedDict as ODict
try:
    import simplejson as json
except ImportError:
    import json

import libnacl
import libnacl.sign

import pytest
from pytest import approx

from bluepea.help.helping import setupTmpBaseDir, cleanupTmpBaseDir
from bluepea.db import dbing


def test_setupDbEnv():
    """

    """
    print("Testing Setup DB Env")

    baseDirPath = setupTmpBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    dbDirPath = os.path.join(baseDirPath, "db/bluepea")
    os.makedirs(dbDirPath)
    assert os.path.exists(dbDirPath)

    env = dbing.setupDbEnv(baseDirPath=dbDirPath)
    assert env.path() == dbDirPath

    assert dbing.dbDirPath == dbDirPath
    assert dbing.dbEnv is env

    data = ODict()

    dbCore = dbing.dbEnv.open_db(b'core')  # open named sub db named 'core' within env

    with dbing.dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
        data["name"] = "John Smith"
        data["city"] = "Alta"
        datab = json.dumps(data, indent=2).encode("utf-8")
        txn.put(b'person0', datab)  # keys and values are bytes
        d0b = txn.get(b'person0')
        assert d0b == datab

        data["name"] = "Betty Smith"
        data["city"] = "Snowbird"
        datab = json.dumps(data, indent=2).encode("utf-8")
        txn.put(b'person1', datab)  # keys and values are bytes
        d1b = txn.get(b'person1')
        assert d1b == datab

        d0b = txn.get(b'person0')  # re-fetch person0
        assert d0b != datab
        data = json.loads(d0b.decode('utf-8'), object_pairs_hook=ODict)
        assert data['name'] == "John Smith"
        assert data['city'] == "Alta"


    cleanupTmpBaseDir(dbDirPath)
    assert not os.path.exists(dbDirPath)
    print("Done Test")

