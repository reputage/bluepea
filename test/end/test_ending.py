from __future__ import generator_stop

import os
import tempfile
import shutil
import binascii
import base64

from collections import OrderedDict as ODict
try:
    import simplejson as json
except ImportError:
    import json

from ioflo.base import storing
import falcon

import pytest
from pytest import approx
import pytest_falcon # declares client fixture

"""
    PyTest fixtures are registered globally in the pytest package
    So any test function can accept a fixture as a parameter supplied by
    the pytest runner

    pytest_falcon assumes there is a fixture named 'app'
"""

import bluepea.end.ending as ending
from bluepea.help.helping import dumpKeys, loadKeys

store = storing.Store(stamp=0.0)

exapp = falcon.API()  # falcon.API instances are callable WSGI apps
ending.loadEnds(exapp, store=store)

@pytest.fixture
def app():
    return exapp

def test_get_AgentRegister(client):  # client is a fixture in pytest_falcon
    """
    Test GET agent/register endpoint with did query parameter
    """
    print("Testing GET /agent/register?did=....")

    rep = client.get('/agent/register?did=did%3Aigo%3Aabcdefghijklmnopqrstuvwxyz')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers == {'content-length': '45', 'content-type': 'application/json; charset=UTF-8'}
    assert rep.body == '{"did": "did:igo:abcdefghijklmnopqrstuvwxyz"}'
    assert rep.json == {'did': 'did:igo:abcdefghijklmnopqrstuvwxyz'}

    print("Done Test")

def test_post_AgentRegister(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing POST /agent/register")

    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": "ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789", }
    body = json.dumps(dict(did="did:igo:abcdefghijklmnopqrstuvwxyz",
                           signer="did:igo:abcdefghijklmnopqurstuvwxyz#0"))
    rep = client.post('/agent/register', body=body, headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.headers == {'content-length': '153', 'content-type': 'application/json; charset=UTF-8'}
    assert rep.body == ('{"data": {"did": "did:igo:abcdefghijklmnopqrstuvwxyz", "signer": '
                        '"did:igo:abcdefghijklmnopqurstuvwxyz#0"}, "sig": '
                        '"ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789"}')
    assert rep.json == {'data': {'did': 'did:igo:abcdefghijklmnopqrstuvwxyz',
                        'signer': 'did:igo:abcdefghijklmnopqurstuvwxyz#0'},
                        'sig': 'ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789'}
    print("Done Test")


def setupBaseDir(baseDirPath=""):
    """
    Create temporary directory
    """
    # create temp directory at /tmp/bluepea...test
    if not baseDirPath:
        baseDirPath = tempfile.mkdtemp(prefix="bluepea",  suffix="test", dir="/tmp")
    baseDirPath = os.path.abspath(os.path.expanduser(baseDirPath))
    return baseDirPath


def cleanupBaseDir(baseDirPath):
    """
    Remove temporary baseDirPath
    """
    if os.path.exists(baseDirPath):
        shutil.rmtree(baseDirPath)



def test_post_AgentRegisterSigned(client):  # client is a fixture in pytest_falcon
    """
    Use libnacl and Base64 to generate compliant signed Agent Registration
    """
    print("Testing POST /agent/register with signature")

    import libnacl
    import libnacl.sign

    signer = signer = libnacl.sign.Signer()  # creates signing/verification key pair
    sigkey = signer.sk  # 64 byte private signing key
    verkey = signer.vk  # 32 byte public verification key
    seed = signer.seed  # random seed used to generate private signing key
    assert seed == signer.sk[:32]

    vk, sk = libnacl.crypto_sign_seed_keypair(seed)  # regenerate keypair from seed
    assert sk == sigkey
    assert vk == verkey

    baseDirPath = setupBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    keyDirPath = os.path.join(baseDirPath, "keys")
    os.makedirs(keyDirPath)
    assert os.path.exists(keyDirPath)
    keyFilePath = os.path.join(keyDirPath, "signer.json")
    assert keyFilePath.endswith("keys/signer.json")

    keyData = ODict(seed=binascii.hexlify(seed).decode('utf-8'),
                    sigkey=binascii.hexlify(sigkey).decode('utf-8'),
                    verkey=binascii.hexlify(verkey).decode('utf-8'))

    dumpKeys(keyData, keyFilePath)
    assert os.path.exists(keyFilePath)

    keyDataFiled = loadKeys(keyFilePath)
    assert keyData == keyDataFiled

    sd = binascii.unhexlify(keyDataFiled['seed'].encode('utf-8'))
    assert sd == seed
    sk = binascii.unhexlify(keyDataFiled['sigkey'].encode('utf-8'))
    assert sk == sigkey
    vk = binascii.unhexlify(keyDataFiled['verkey'].encode('utf-8'))
    assert vk == verkey


    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": "ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789", }
    body = json.dumps(dict(did="did:igo:abcdefghijklmnopqrstuvwxyz",
                           signer="did:igo:abcdefghijklmnopqurstuvwxyz#0"))
    rep = client.post('/agent/register', body=body, headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.headers == {'content-length': '153', 'content-type': 'application/json; charset=UTF-8'}
    assert rep.body == ('{"data": {"did": "did:igo:abcdefghijklmnopqrstuvwxyz", "signer": '
                        '"did:igo:abcdefghijklmnopqurstuvwxyz#0"}, "sig": '
                        '"ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789"}')
    assert rep.json == {'data': {'did': 'did:igo:abcdefghijklmnopqrstuvwxyz',
                        'signer': 'did:igo:abcdefghijklmnopqurstuvwxyz#0'},
                        'sig': 'ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789'}

    cleanupBaseDir(baseDirPath)
    print("Done Test")
