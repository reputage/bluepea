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
from bluepea.help.helping import setupTmpBaseDir, cleanupTmpBaseDir

from bluepea.keep import keeping


def test_setupKeep():
    """
    Test setting up keep directory
    """
    print("Testing setupKeep")

    baseDirPath = setupTmpBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    keepDirPath = os.path.join(baseDirPath, "keep/bluepea")
    os.makedirs(keepDirPath)
    assert os.path.exists(keepDirPath)

    gKeepDirPath = keeping.setupKeep(baseDirPath=keepDirPath)

    assert gKeepDirPath == keepDirPath
    assert gKeepDirPath == keeping.KeepDirPath

    cleanupTmpBaseDir(keepDirPath)
    assert not os.path.exists(keepDirPath)
    print("Done Test")

def test_setupTestKeep():
    """
    Test setting up test Keep directory
    """
    print("Testing setupTestKeep")

    keepDirPath = keeping.setupTestKeep()
    assert keepDirPath.startswith("/tmp/bluepea")
    assert keepDirPath.endswith("test/keep/bluepea")
    assert os.path.exists(keepDirPath)
    assert keepDirPath == keeping.KeepDirPath
    cleanupTmpBaseDir(keepDirPath)
    assert not os.path.exists(keepDirPath)
    print("Done Test")

def test_dumpLoadKeys():
    """

    """
    print("Testing dump load keys")

    baseDirPath = setupTmpBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    keyDirPath = os.path.join(baseDirPath, "keys")
    os.makedirs(keyDirPath)
    assert os.path.exists(keyDirPath)
    keyFilePath = os.path.join(keyDirPath, "signer.json")
    assert keyFilePath.endswith("keys/signer.json")

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    assert seed == sigkey[:32]
    assert verkey == (b'B\xdd\xbb}8V\xa0\xd6lk\xcf\x15\xad9\x1e\xa7\xa1\xfe\xe0p<\xb6\xbex'
                      b'\xb0s\x8d\xd6\xf5\xa5\xe8Q')
    assert sigkey == (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
                      b'\xf2K\x93`B\xdd\xbb}8V\xa0\xd6lk\xcf\x15\xad9\x1e\xa7\xa1\xfe\xe0p<\xb6\xbex'
                      b'\xb0s\x8d\xd6\xf5\xa5\xe8Q')


    keyData = ODict(seed=binascii.hexlify(seed).decode('utf-8'),
                    sigkey=binascii.hexlify(sigkey).decode('utf-8'),
                    verkey=binascii.hexlify(verkey).decode('utf-8'))

    assert keyData == ODict([
        ('seed',
            '50546915d5d360f175157d5e729b6648026cc61b1d1c0b39d77bc05ff24b9360'),
        ('sigkey',
            ('50546915d5d360f175157d5e729b6648026cc61b1d1c0b39d77bc05ff24b93604'
             '2ddbb7d3856a0d66c6bcf15ad391ea7a1fee0703cb6be78b0738dd6f5a5e851')),
        ('verkey',
            '42ddbb7d3856a0d66c6bcf15ad391ea7a1fee0703cb6be78b0738dd6f5a5e851')
        ])

    keeping.dumpKeys(keyData, keyFilePath)
    assert os.path.exists(keyFilePath)
    mode = stat.filemode(os.stat(keyFilePath).st_mode)
    assert mode == "-rw-------"

    keyDataFiled = keeping.loadKeys(keyFilePath)
    assert keyData == keyDataFiled

    sd = binascii.unhexlify(keyDataFiled['seed'].encode('utf-8'))
    assert sd == seed
    sk = binascii.unhexlify(keyDataFiled['sigkey'].encode('utf-8'))
    assert sk == sigkey
    vk = binascii.unhexlify(keyDataFiled['verkey'].encode('utf-8'))
    assert vk == verkey

    cleanupTmpBaseDir(baseDirPath)
    assert not os.path.exists(keyFilePath)
    print("Done Test")
