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

def test_Keeper():
    """
    Test Keeper class
    """
    print("Testing Keeper Class")

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

    keeper = keeping.Keeper(baseDirPath=keepDirPath, seed=seed, prikey=prikey)

    assert keeper.baseDirPath == keepDirPath
    assert keeper.filePath.endswith("/bluepea/keep/key.server.json")

    assert keeper.seed == seed
    assert keeper.sigkey == (b'\x0c\xaa\xc9\xc6G\x11\xf6nn\xd7\x1b7\xdc^i\xc5\x12O\xe9>\xe1$F\xe1'
                             b'\xa4z\xd4\xb6P\xdd\x86\x1d^\xaeX\xa9\xa2\xfa/\x8f)\x7fG\xee\xec\x85!/BQiM'
                             b"\xbfG\x11O\xd0\x02\xf8\xdf\x06'\xd7\x8f")
    assert keeper.sigkey[:32] == keeper.seed
    assert keeper.verkey == (b'^\xaeX\xa9\xa2\xfa/\x8f)\x7fG\xee\xec\x85!/BQiM\xbfG\x11O\xd0\x02\xf8\xdf'
                             b"\x06'\xd7\x8f")


    keys = keeper.loadAllRoles(keeper.baseDirPath)
    assert "server" in keys
    assert keys['server']['seed'] == '0caac9c64711f66e6ed71b37dc5e69c5124fe93ee12446e1a47ad4b650dd861d'
    assert keys['server']['prikey'] == 'd9c83c2403b9250363b32a3667a76dd88d086ad45e3488ca63bad1e9d9e69925'

    keeper.clearBaseDir()
    assert not os.path.exists(keepDirPath)

    cleanupTmpBaseDir(os.path.dirname(keepDirPath))
    assert not os.path.exists(os.path.dirname(keepDirPath))
    print("Done Test")


def test_setupKeeper():
    """
    Test setting up keep directory
    """
    print("Testing setupKeeper")

    seed = (b'\x0c\xaa\xc9\xc6G\x11\xf6nn\xd7\x1b7\xdc^i\xc5\x12O\xe9>\xe1$F\xe1'
            b'\xa4z\xd4\xb6P\xdd\x86\x1d')

    prikey = (b'\xd9\xc8<$\x03\xb9%\x03c\xb3*6g\xa7m\xd8\x8d\x08j\xd4^4\x88\xcac\xba\xd1\xe9'
              b'\xd9\xe6\x99%')

    baseDirPath = setupTmpBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    keepDirPath = os.path.join(baseDirPath, "bluepea/keep")
    os.makedirs(keepDirPath)
    assert os.path.exists(keepDirPath)

    keeper = keeping.setupKeeper(baseDirPath=keepDirPath, seed=seed, prikey=prikey)

    assert keeper == keeping.gKeeper
    assert keeper.baseDirPath == keeping.gKeepDirPath

    cleanupTmpBaseDir(keepDirPath)
    assert not os.path.exists(keepDirPath)
    print("Done Test")

def test_setupTestKeeper():
    """
    Test setting up test Keep directory
    """
    print("Testing setupTestKeep")

    keeper = keeping.setupTestKeeper()
    assert keeper == keeping.gKeeper

    assert keeper.seed == (b'\x0c\xaa\xc9\xc6G\x11\xf6nn\xd7\x1b7\xdc^i\xc5\x12O\xe9>\xe1$F\xe1'
            b'\xa4z\xd4\xb6P\xdd\x86\x1d')

    assert keeper.prikey == (b'\xd9\xc8<$\x03\xb9%\x03c\xb3*6g\xa7m\xd8\x8d\x08j\xd4^4\x88\xcac\xba\xd1\xe9'
              b'\xd9\xe6\x99%')


    assert keeper.baseDirPath == keeping.gKeepDirPath
    assert keeper.baseDirPath.startswith("/tmp/bluepea")
    assert keeper.baseDirPath.endswith("test/bluepea/keep")
    assert os.path.exists(keeper.baseDirPath)

    cleanupTmpBaseDir(keeper.baseDirPath)
    assert not os.path.exists(keeper.baseDirPath)
    print("Done Test")


def test_setupKeep():
    """
    Test setting up keep directory
    """
    print("Testing setupKeep")

    baseDirPath = setupTmpBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    keepDirPath = os.path.join(baseDirPath, "bluepea/keep")
    os.makedirs(keepDirPath)
    assert os.path.exists(keepDirPath)

    gKeepDirPath = keeping.setupKeep(baseDirPath=keepDirPath)

    assert gKeepDirPath == keepDirPath
    assert gKeepDirPath == keeping.gKeepDirPath

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
    assert keepDirPath.endswith("test/bluepea/keep")
    assert os.path.exists(keepDirPath)
    assert keepDirPath == keeping.gKeepDirPath
    cleanupTmpBaseDir(keepDirPath)
    assert not os.path.exists(keepDirPath)
    print("Done Test")

def test_loadAllKeys():
    """
    Test loading all key files from directory
    """
    print("Testing loadAllKeys")

    keepDirPath = keeping.setupTestKeep()
    assert keepDirPath.startswith("/tmp/bluepea")
    assert keepDirPath.endswith("test/bluepea/keep")
    assert os.path.exists(keepDirPath)
    assert keepDirPath == keeping.gKeepDirPath

    prefix = "server"
    keyFilePath = os.path.join(keepDirPath, "key.{}.json".format(prefix))
    assert keyFilePath.endswith("/bluepea/keep/key.{}.json".format(prefix))

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


    keys = ODict(seed=binascii.hexlify(seed).decode('utf-8'),
                    sigkey=binascii.hexlify(sigkey).decode('utf-8'),
                    verkey=binascii.hexlify(verkey).decode('utf-8'))

    assert keys == ODict([
        ('seed',
         '50546915d5d360f175157d5e729b6648026cc61b1d1c0b39d77bc05ff24b9360'),
        ('sigkey',
         ('50546915d5d360f175157d5e729b6648026cc61b1d1c0b39d77bc05ff24b93604'
             '2ddbb7d3856a0d66c6bcf15ad391ea7a1fee0703cb6be78b0738dd6f5a5e851')),
        ('verkey',
         '42ddbb7d3856a0d66c6bcf15ad391ea7a1fee0703cb6be78b0738dd6f5a5e851')
    ])

    keeping.dumpKeys(keys, keyFilePath)
    assert os.path.exists(keyFilePath)
    mode = stat.filemode(os.stat(keyFilePath).st_mode)
    assert mode == "-rw-------"

    roles = keeping.loadAllKeyRoles(keepDirPath)
    assert prefix in roles
    assert roles[prefix] == keys  # round trip

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

