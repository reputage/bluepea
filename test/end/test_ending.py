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
from bluepea.bluepeaing import SEPARATOR_BYTES

from bluepea.help.helping import (key64uToKey, keyToKey64u, makeDid,
                                  verify, verify64u, parseSignatureHeader,
                                  setupTmpBaseDir, cleanupTmpBaseDir,
                                  makeSignedAgentReg, makeSignedThingReg,
                                  )
from bluepea.db.dbing import setupTestDbEnv

import bluepea.db.dbing as dbing
import bluepea.keep.keeping as keeping
import bluepea.prime.priming as priming
import bluepea.end.ending as ending

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
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"
    assert arrow.get(stamp).datetime == dt

    hid = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    hids = [hid]  # list of hids

    signature, registration = makeSignedAgentReg(vk,
                                                 sk,
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
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"
    assert arrow.get(stamp).datetime == dt

    hidspace = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    hids = [hidspace]  # list of hids

    signature, registration = makeSignedAgentReg(svk,
                                                 ssk,
                                                 changed=stamp,
                                                 hids=hids)


    # version without posting agent creation just put in database
    #did = result['did']  # unicode version
    #didb = did.encode("utf-8")  # bytes version

    ## save to database
    #dbEnv = dbing.DbEnv  # lmdb database env assumes already setup
    #dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
    #with dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
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

    areg = rep.json

    assert areg ==  {
        'did': 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
        'signer': 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0',
        'changed': '2000-01-01T00:00:00+00:00',
        'keys':
        [
            {
                'key': 'Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
                'kind': 'EdDSA'
            }
        ],
        'hids':
        [
            {
                'issuer': 'generic.com',
                'kind': 'dns',
                'registered': '2000-01-01T00:00:00+00:00',
                'validationURL': 'https://generic.com/indigo'
            }
         ]
    }

    # creates signing/verification key pair thing DID
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
            b'P\xdd&R <\x97\x01')


    dvk, dsk = libnacl.crypto_sign_seed_keypair(seed)
    assert dvk == (b'\xe0\x90\x8c\xf1\xd2V\xc3\xf3\xb9\xee\xf38\x90\x0bS\xb7L\x96\xa9('
                   b'\x01\xbb\x08\x87\xa5X\x1d\xe7\x90b\xa0#')
    assert dsk == (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
                    b'P\xdd&R <\x97\x01\xe0\x90\x8c\xf1\xd2V\xc3\xf3\xb9\xee\xf38\x90\x0bS\xb7'
                    b'L\x96\xa9(\x01\xbb\x08\x87\xa5X\x1d\xe7\x90b\xa0#')


    signer = areg['signer']
    hid = "hid:dns:generic.com#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    dsignature, ssignature, tregistration = makeSignedThingReg(dvk,
                                                               dsk,
                                                               ssk,
                                                               signer,
                                                               changed=stamp,
                                                               hid=hid,
                                                               data=data)


    assert tregistration == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:generic.com#02",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",\n'
        '  "changed": "2000-01-01T00:00:00+00:00",\n'
        '  "data": {\n'
        '    "keywords": [\n'
        '      "Canon",\n'
        '      "EOS Rebel T6",\n'
        '      "251440"\n'
        '    ],\n'
        '    "message": "If found please return."\n'
        '  }\n'
        '}')

    assert dsignature == ('kWZwPfepoAV9zyt9B9vPlPNGeb_POHlP9LL3H-PH71WWZzVJT1Ce'
                          '64IKj1GmOXkNo2JaXrnIpQyfm2vynn7mCg==')

    assert ssignature == ('RtlBu9sZgqhfc0QbGe7IHqwsHOARrGNjy4BKJG7gNfNP4GfKDQ8F'
                          'Gdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg==')

    treg = json.loads(tregistration, object_pairs_hook=ODict)

    assert treg == {
      "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
      "hid": "hid:dns:generic.com#02",
      "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
      "changed": "2000-01-01T00:00:00+00:00",
      "data":
      {
        "keywords": ["Canon", "EOS Rebel T6", "251440"],
        "message": "If found please return.",
      }
    }

    headers = {
        "Content-Type": "text/html; charset=utf-8",
        "Signature": 'signer="{}";did="{}"'.format(ssignature, dsignature),
    }

    body = tregistration  # client.post encodes the body

    rep = client.post('/thing/register', body=body, headers=headers)
    assert rep.status == falcon.HTTP_201
    assert treg == rep.json

    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/thing/register?did=did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="

    path, query = location.rsplit("?", maxsplit=1)
    assert query == "did=did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="

    query = falcon.uri.parse_query_string(query)
    tdid = query['did']
    assert tdid == "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="

    assert rep.headers['content-type'] == "application/json; charset=UTF-8"

    assert treg["did"] == tdid

    dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
    with dbEnv.begin(db=dbCore) as txn:  # txn is a Transaction object
        rsrcb = txn.get(tdid.encode('utf-8'))  # keys are bytes
    assert rsrcb
    datab, sep, signatureb = rsrcb.partition(SEPARATOR_BYTES)
    data = json.loads(datab.decode("utf-8"), object_pairs_hook=ODict)
    datau = datab.decode("utf-8")
    assert data == treg
    assert signatureb.decode("utf-8") == ssignature
    assert datau == tregistration
    sverkey = keyToKey64u(svk)
    assert sverkey == 'Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='

    result = verify64u(signature=ssignature,
                       message=datau,
                       verkey=sverkey)

    assert result

    # verify hid table entry
    dbHid2Did = dbEnv.open_db(b'hid2did')  # open named sub db named 'hid2did' within env
    with dbEnv.begin(db=dbHid2Did) as txn:  # txn is a Transaction object
        tdidb = txn.get(treg['hid'].encode("utf-8"))  # keys are bytes

    assert tdidb.decode("utf-8") == tdid

    print("Testing GET /thing/register?did=....")

    didURI = falcon.uri.encode_value(tdid)
    rep = client.get('/thing/register?did={}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 349
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="RtlBu9sZgqhfc0QbGe7IHqwsHOARrG'
                'Njy4BKJG7gNfNP4GfKDQ8FGdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg=="')
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == ssignature

    assert rep.body == tregistration
    assert rep.json == treg

    assert verify64u(ssignature, tregistration, sverkey)

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_get_AgentServer(client):  # client is a fixture in pytest_falcon
    """
    Test GET to retrieve precreated server agent.
    """
    print("Testing GET /agent/register with signature")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    did = keeper.did

    print("Testing GET /agent/server")

    rep = client.get('/agent/server')

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 291
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="u72j9aKHgz99f0K8pSkMnyqwvEr_3r'
                'pS_z2034L99sTWrMIIJGQPbVuIJ1cupo6cfIf_KCB5ecVRYoFRzAPnAQ=="')
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == ('u72j9aKHgz99f0K8pSkMnyqwvEr_3rpS_z2034L99sTWrMII'
                              'JGQPbVuIJ1cupo6cfIf_KCB5ecVRYoFRzAPnAQ==')

    assert rep.body == (
        '{\n'
        '  "did": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=",\n'
        '  "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",\n'
        '  "changed": "2000-01-01T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ]\n'
        '}')

    assert rep.json == {
        'did': 'did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=',
        'signer': 'did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0',
        'changed': '2000-01-01T00:00:00+00:00',
        'keys':
        [
            {
                'key': 'Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=',
                'kind': 'EdDSA'
            }
        ],
    }

    assert rep.json['did'] == did

    assert verify64u(sigs['signer'], rep.body, rep.json['keys'][0]['key'])

    dat, ser, sig = dbing.getSigned(did)

    assert dat == rep.json
    assert ser == rep.body
    assert sig == sigs['signer']

    print("Testing get server using GET /agent/registration?did=")

    didURI = falcon.uri.encode_value(did)
    rep = client.get('/agent/register?did={}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 291
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="u72j9aKHgz99f0K8pSkMnyqwvEr_3r'
                    'pS_z2034L99sTWrMIIJGQPbVuIJ1cupo6cfIf_KCB5ecVRYoFRzAPnAQ=="')
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == sig
    assert rep.body == ser
    assert rep.json == dat

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")
