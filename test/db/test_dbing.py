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

from bluepea.bluepeaing import SEPARATOR
from bluepea.help.helping import (setupTmpBaseDir, cleanupTmpBaseDir,
                                  makeSignedAgentReg)

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


def test_putSigned_getSelfSigned():
    """
    Test putSigned and getSelfSigned
    """
    print("Testing utSigned and getSelfSigned")

    dbEnv = dbing.setupTestDbEnv()

    # Create self signed resource
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    sig, ser = makeSignedAgentReg(vk, sk, changed=stamp)

    assert len(sig) == 88
    assert sig == ('AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKBYrPP'
                         'xAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg==')

    assert len(ser) == 291
    assert SEPARATOR not in ser  # separator
    assert ser == (
        '{\n'
        '  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",\n'
        '  "changed": "2000-01-01T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ]\n'
        '}')

    dat = json.loads(ser, object_pairs_hook=ODict)
    did = dat['did']

    assert did == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    dbing.putSigned(ser, sig, did)

    gdat, gser, gsig = dbing.getSelfSigned(did)

    assert gdat == dat
    assert gser == ser
    assert gsig == sig


    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")
