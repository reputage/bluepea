from __future__ import generator_stop

import os
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

import arrow

import libnacl
import libnacl.sign

from ioflo.base import storing
from ioflo.aid import timing
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
from bluepea.help.helping import (dumpKeys, loadKeys,
                                  key64uToKey, keyToKey64u, makeDid,
                                  verify, verify64u, parseSignatureHeader,
                                  setupTmpBaseDir, cleanupTmpBaseDir,
                                  makeSignedAgentReg, SEPARATOR_BYTES)
from bluepea.db.dbing import setupTestDbEnv

store = storing.Store(stamp=0.0)

exapp = falcon.API()  # falcon.API instances are callable WSGI apps
ending.loadEnds(exapp, store=store)

@pytest.fixture
def app():
    return exapp


def test_post_AgentRegisterSigned(client):  # client is a fixture in pytest_falcon
    """
    Use libnacl and Base64 to generate compliant signed Agent Registration
    Test both POST to create resource and subsequent GET to retrieve it.
    """
    print("Testing POST /agent/register with signature")

    dbEnv = setupTestDbEnv()

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    assert arrow.get(stamp).datetime == dt

    signature, registration = makeSignedAgentReg(verkey, sigkey, changed=stamp)

    assert signature == ('AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKBYrPPx'
                         'AoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg==')

    assert registration == (
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


    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(signature), }

    assert headers['Signature'] == ('signer="AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6'
                    'wiIGpVNJQQoYKBYrPPxAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg=="')

    body = registration  # client.post encodes the body

    rep = client.post('/agent/register', body=body, headers=headers)

    assert rep.status == falcon.HTTP_201

    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/agent/register?did=did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    path, query = location.rsplit("?", maxsplit=1)
    assert query == "did=did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    query = falcon.uri.parse_query_string(query)
    did = query['did']
    assert did == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    assert rep.headers['content-type'] == "application/json; charset=UTF-8"

    reg = rep.json
    assert reg["did"] == did
    assert reg == {
      'changed': '2000-01-01T00:00:00+00:00',
      'did': 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
      'keys':
      [
        {
          'key': 'Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
          'kind': 'EdDSA'
        }
      ],
      'signer': 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0'
    }

    dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env

    with dbEnv.begin(db=dbCore) as txn:  # txn is a Transaction object
        rsrcb = txn.get(reg['did'].encode('utf-8'))  # keys are bytes

    assert rsrcb

    datab, sep, signatureb = rsrcb.partition(SEPARATOR_BYTES)

    data = json.loads(datab.decode("utf-8"), object_pairs_hook=ODict)
    assert data == reg
    assert signatureb.decode("utf-8") == signature

    assert verify64u(signature=signatureb.decode("utf-8"),
                     message=datab.decode("utf-8"),
                     verkey=reg["keys"][0]["key"])


    print("Testing GET /agent/register?did=....")

    didURI = falcon.uri.encode_value(did)
    rep = client.get('/agent/register?did={}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 291
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6'
                    'wiIGpVNJQQoYKBYrPPxAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg=="')
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == signature

    assert rep.body == registration
    assert rep.json == reg

    assert verify64u(signature, registration, reg['keys'][0]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_post_IssuerRegisterSigned(client):  # client is a fixture in pytest_falcon
    """
    Use libnacl and Base64 to generate compliant signed Agent Registration
    Test both POST to create resource and subsequent GET to retrieve it.
    """
    print("Testing Issuer creation POST /agent/register with signature ")

    dbEnv = setupTestDbEnv()

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"
    assert arrow.get(stamp).datetime == dt

    hid = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    hids = [hid]  # list of hids

    signature, registration = makeSignedAgentReg(verkey,
                                                 sigkey,
                                                 changed=stamp,
                                                 hids=hids)
    assert signature == ('f2w1L6XtU8_GS5N8UwX0d77aw2kR0IM5BVdBLOaoIyR9nzra6d4Jg'
                         'VV7TlJrEx8WhJlgBRpyInRZgdnSf_WQAg==')

    assert registration == (
        '{\n'
        '  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",\n'
        '  "changed": "2000-01-01T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ],\n'
        '  "hids": [\n'
        '    {\n'
        '      "kind": "dns",\n'
        '      "issuer": "generic.com",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "https://generic.com/indigo"\n'
        '    }\n'
        '  ]\n'
        '}')


    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(signature), }

    assert headers['Signature'] == ('signer="f2w1L6XtU8_GS5N8UwX0d77aw2kR0IM5BV'
                    'dBLOaoIyR9nzra6d4JgVV7TlJrEx8WhJlgBRpyInRZgdnSf_WQAg=="')

    body = registration  # client.post encodes the body

    rep = client.post('/agent/register', body=body, headers=headers)

    assert rep.status == falcon.HTTP_201

    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/agent/register?did=did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    path, query = location.rsplit("?", maxsplit=1)
    assert query == "did=did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    query = falcon.uri.parse_query_string(query)
    did = query['did']
    assert did == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    assert rep.headers['content-type'] == "application/json; charset=UTF-8"

    reg = rep.json
    assert reg["did"] == did
    assert reg == {'changed': '2000-01-01T00:00:00+00:00',
                    'did': 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
                    'hids': [{'issuer': 'generic.com',
                              'kind': 'dns',
                              'registered': '2000-01-01T00:00:00+00:00',
                              'validationURL': 'https://generic.com/indigo'}],
                    'keys': [{'key': 'Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
                              'kind': 'EdDSA'}],
                    'signer': 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0'}

    dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env

    with dbEnv.begin(db=dbCore) as txn:  # txn is a Transaction object
        rsrcb = txn.get(reg['did'].encode('utf-8'))  # keys are bytes

    assert rsrcb

    datab, sep, signatureb = rsrcb.partition(SEPARATOR_BYTES)

    data = json.loads(datab.decode("utf-8"), object_pairs_hook=ODict)
    assert data == reg
    assert signatureb.decode("utf-8") == signature

    assert verify64u(signature=signatureb.decode("utf-8"),
                     message=datab.decode("utf-8"),
                     verkey=reg["keys"][0]["key"])


    print("Testing GET /agent/register?did=....")

    didURI = falcon.uri.encode_value(did)
    rep = client.get('/agent/register?did={}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 473
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="f2w1L6XtU8_GS5N8UwX0d77aw2kR0IM5BV'
                    'dBLOaoIyR9nzra6d4JgVV7TlJrEx8WhJlgBRpyInRZgdnSf_WQAg=="')
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == signature

    assert rep.body == registration
    assert rep.json == reg

    assert verify64u(signature, registration, reg['keys'][0]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_post_ThingRegisterSigned(client):  # client is a fixture in pytest_falcon
    """
    Use libnacl and Base64 to generate compliant signed Thing Registration
    Test both POST to create resource and subsequent GET to retrieve it.

    Does an Agent registration to setup database
    """
    print("Testing Thing creation POST /agent/register with signature ")

    dbEnv = setupTestDbEnv()

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"
    assert arrow.get(stamp).datetime == dt

    hid = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    hids = [hid]  # list of hids

    signature, registration = makeSignedAgentReg(verkey,
                                                 sigkey,
                                                 changed=stamp,
                                                 hids=hids)


    # version without posting agent creation just put in database
    #did = result['did']  # unicode version
    #didb = did.encode("utf-8")  # bytes version

    ## save to database
    #dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
    #dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
    #with dbing.dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
        #rsrcb = txn.get(didb)
        #if rsrcb is not None:  # must not be pre-existing
            #raise falcon.HTTPError(falcon.HTTP_412,
                                   #'Preexistence Error',
                                   #'DID already exists')
        #resource = registration + SEPARATOR + signer
        #txn.put(didb, resource.encode("utf-8") )  # keys and values are bytes

    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(signature), }

    body = registration  # client.post encodes the body

    rep = client.post('/agent/register', body=body, headers=headers)
    assert rep.status == falcon.HTTP_201



    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")
