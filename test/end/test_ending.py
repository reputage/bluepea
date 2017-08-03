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
from bluepea.bluepeaing import SEPARATOR_BYTES, PROPAGATION_DELAY

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

def setupTestDbAgentsThings():
    """
    Put test agents and things in db and return duple of dicts (agents, things)
    keyed by  name each value is triple ( did, vk, sk)  where
    vk is public verification key
    sk is private signing key
    """
    agents = ODict()
    things = ODict()

    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    changed = timing.iso8601(dt, aware=True)

    # make "ann" the agent
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    avk, ask = libnacl.crypto_sign_seed_keypair(seed)

    sig, ser = makeSignedAgentReg(avk, ask, changed=changed)

    adat = json.loads(ser, object_pairs_hook=ODict)
    adid = adat['did']

    dbing.putSigned(key=adid, ser=ser, sig=sig, clobber=False)

    agents['ann'] = (adid, avk, ask)

    # make "ivy" the issurer
    seed = seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
                   b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    ivk, isk = libnacl.crypto_sign_seed_keypair(seed)

    issuant = ODict(kind="dns",
                issuer="generic.com",
                registered=changed,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of issuants hid name spaces

    sig, ser = makeSignedAgentReg(ivk, isk, changed=changed, issuants=issuants)

    idat = json.loads(ser, object_pairs_hook=ODict)
    idid = idat['did']

    dbing.putSigned(key=idid, ser=ser, sig=sig, clobber=False)

    agents['ivy'] = (idid, ivk, isk)

    # make "cam" the thing
    # create  thing signed by issuer and put into database
    seed = (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
            b'P\xdd&R <\x97\x01')

    cvk, csk = libnacl.crypto_sign_seed_keypair(seed)

    signer = idat['signer']  # use same signer key fragment reference as issuer isaac
    hid = "hid:dns:generic.com#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    sig, isig, ser = makeSignedThingReg(cvk,
                                          csk,
                                            isk,
                                            signer,
                                            changed=changed,
                                            hid=hid,
                                            data=data)

    cdat = json.loads(ser, object_pairs_hook=ODict)
    cdid = cdat['did']

    dbing.putSigned(key=cdid, ser=ser, sig=isig, clobber=False)

    things['cam'] = (cdid, cvk, csk)

    # make "fae" the finder
    seed = (b'\xf9\x13\xf0\xff\xd4\xb3\xbdF\xa2\x80\x1d\xce\xaa\xd9\x87df\xc8\x1f\x91'
            b';\x9bp+\x1bK\x1ey\xef6\xa7\xf9')


    # creates signing/verification key pair
    fvk, fsk = libnacl.crypto_sign_seed_keypair(seed)

    sig, ser = makeSignedAgentReg(fvk, fsk, changed=changed)

    fdat = json.loads(ser, object_pairs_hook=ODict)
    fdid = fdat['did']

    dbing.putSigned(key=fdid, ser=ser, sig=sig,  clobber=False)

    agents['fae'] = (fdid, fvk, fsk)

    return (agents, things)


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

    rep = client.post('/agent', body=body, headers=headers)

    assert rep.status == falcon.HTTP_201

    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/agent?did=did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

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


    print("Testing GET /agent?did=....")

    didURI = falcon.uri.encode_value(did)
    rep = client.get('/agent?did={}'.format(didURI))

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
    seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
            b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"
    assert arrow.get(stamp).datetime == dt

    issuant = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of hids

    signature, registration = makeSignedAgentReg(vk,
                                                 sk,
                                                 changed=stamp,
                                                 issuants=issuants)
    assert signature == ('xZbsn-GqZQZmZX9UdhbG45EEGGj25o7WJ_t7yYI9UfXXseV7my3faYhn4slrxB-KuujOMjFmx_EJaZWgGb8HCg==')

    assert registration == (
        '{\n'
        '  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",\n'
        '  "changed": "2000-01-01T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ],\n'
        '  "issuants": [\n'
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

    assert headers['Signature'] == ('signer="xZbsn-GqZQZmZX9UdhbG45EEGGj25o7WJ_t7yYI9UfXXseV7my3faYhn4slrxB-KuujOMjFmx_EJaZWgGb8HCg=="')

    body = registration  # client.post encodes the body

    rep = client.post('/agent', body=body, headers=headers)

    assert rep.status == falcon.HTTP_201

    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/agent?did=did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="

    path, query = location.rsplit("?", maxsplit=1)
    assert query == "did=did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="

    query = falcon.uri.parse_query_string(query)
    did = query['did']
    assert did == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="

    assert rep.headers['content-type'] == "application/json; charset=UTF-8"

    reg = rep.json
    assert reg["did"] == did
    assert reg == {'changed': '2000-01-01T00:00:00+00:00',
                    'did': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=',
                    'issuants': [{'issuer': 'generic.com',
                              'kind': 'dns',
                              'registered': '2000-01-01T00:00:00+00:00',
                              'validationURL': 'https://generic.com/indigo'}],
                    'keys': [{'key': 'dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=',
                              'kind': 'EdDSA'}],
                    'signer': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0'}

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


    print("Testing GET /agent?did=....")

    didURI = falcon.uri.encode_value(did)
    rep = client.get('/agent?did={}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 477
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="xZbsn-GqZQZmZX9UdhbG45EEGGj25o7WJ_t7yYI9UfXXseV7my3faYhn4slrxB-KuujOMjFmx_EJaZWgGb8HCg=="')
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
    print("Testing Thing creation POST /thing with signature ")

    dbEnv = setupTestDbEnv()

    # First create the controlling agent for thing
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
            b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"
    assert arrow.get(stamp).datetime == dt

    issuant = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of issuants of hid name spaces

    signature, registration = makeSignedAgentReg(svk,
                                                 ssk,
                                                 changed=stamp,
                                                 issuants=issuants)


    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(signature), }

    body = registration  # client.post encodes the body

    rep = client.post('/agent', body=body, headers=headers)
    assert rep.status == falcon.HTTP_201

    areg = rep.json

    assert areg ==  {
        'did': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=',
        'signer': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0',
        'changed': '2000-01-01T00:00:00+00:00',
        'keys':
        [
            {
                'key': 'dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=',
                'kind': 'EdDSA'
            }
        ],
        'issuants':
        [
            {
                'issuer': 'generic.com',
                'kind': 'dns',
                'registered': '2000-01-01T00:00:00+00:00',
                'validationURL': 'https://generic.com/indigo'
            }
         ]
    }

    # Now create the thing
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
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",\n'
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

    assert dsignature == ('3VUjzx_5uigvwFAv0FNYl9rlZL1g5KKSqPAIAOENXdwW14vigTxc'
                          'tQnQgHlfF4JBvyIha43WiDrb45Gspa2RDA==')

    assert ssignature == ('bNUB37pBC5KuSVx4SKw8qQGR405wH7qNI2pjv2MhmyqsJ8ofTTS2'
                          'WYs3ZaU7aDyoJGSIfwJcadmcok9tntdkDA==')

    treg = json.loads(tregistration, object_pairs_hook=ODict)

    assert treg == {
      "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
      "hid": "hid:dns:generic.com#02",
      "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
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

    rep = client.post('/thing', body=body, headers=headers)
    assert rep.status == falcon.HTTP_201
    assert treg == rep.json

    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/thing?did=did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="

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
    assert sverkey == 'dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY='

    result = verify64u(signature=ssignature,
                       message=datau,
                       verkey=sverkey)

    assert result

    # verify hid table entry
    dbHid2Did = dbEnv.open_db(b'hid2did')  # open named sub db named 'hid2did' within env
    with dbEnv.begin(db=dbHid2Did) as txn:  # txn is a Transaction object
        tdidb = txn.get(treg['hid'].encode("utf-8"))  # keys are bytes

    assert tdidb.decode("utf-8") == tdid

    print("Testing GET /thing?did=....")

    didURI = falcon.uri.encode_value(tdid)
    rep = client.get('/thing?did={}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 349
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="bNUB37pBC5KuSVx4SKw8qQGR405wH7'
                    'qNI2pjv2MhmyqsJ8ofTTS2WYs3ZaU7aDyoJGSIfwJcadmcok9tntdkDA=="')
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
    print("Testing GET /server with signature")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    print("Testing GET /server")

    rep = client.get('/server')

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

    assert rep.json['did'] == kdid

    assert verify64u(sigs['signer'], rep.body, rep.json['keys'][0]['key'])

    dat, ser, sig = dbing.getSigned(kdid)

    assert dat == rep.json
    assert ser == rep.body
    assert sig == sigs['signer']

    print("Testing get server using GET /agent/registration?did=")

    didURI = falcon.uri.encode_value(kdid)
    rep = client.get('/agent?did={}'.format(didURI))

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


def test_get_AgentDid(client):  # client is a fixture in pytest_falcon
    """
    Test GET to agent at did.
    """
    print("Testing GET /agent/{did}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    # put agent into database
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)

    sig, res = makeSignedAgentReg(vk, sk, changed=stamp)

    reg = json.loads(res, object_pairs_hook=ODict)
    did = reg['did']

    dbing.putSigned(key=did, ser=res, sig=sig, clobber=False)


    didURI = falcon.uri.encode_value(did)
    rep = client.get('/agent/{}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert int(rep.headers['content-length']) == 291
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="{}"'.format(sig))
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == ('AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKB'
                              'YrPPxAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg==')

    assert rep.body == (
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


    assert rep.json['did'] == did
    assert verify64u(sigs['signer'], rep.body, rep.json['keys'][0]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_put_AgentDid(client):  # client is a fixture in pytest_falcon
    """
    Test PUT to agent at did.
    Overwrites existing agent data resource with new data
    """
    print("Testing put /agent/{did}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    # put an agent into database so we can update it
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)

    sig, res = makeSignedAgentReg(vk, sk, changed=stamp)

    reg = json.loads(res, object_pairs_hook=ODict)
    did = reg['did']

    dbing.putSigned(key=did, ser=res, sig=sig, clobber=False)

    rdat, rser, rsig = dbing.getSelfSigned(did)

    assert rdat == reg
    assert rser == res
    assert rsig == sig

    # change signer and key fields
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'\xd2\'\x87\x0fs\xd7\xf5\xba\xc1\xff!\x85j\xf5\xe4"\x87\x1c8\n[\xe9\x8e\x0b'
            b'\x11\xf55\x8b\xb8\x0c\x19\x13')

    # creates signing/verification key pair
    nvk, nsk = libnacl.crypto_sign_seed_keypair(seed)

    ndt = datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc)
    nstamp = timing.iso8601(ndt, aware=True)

    index = 1
    signer = "{}#{}".format(did, index)  # signer field value key at index
    nverkey = keyToKey64u(nvk)  # make key index field value
    assert nverkey == 'FsSQTQnp_W-6RPkuvULH8h8G5u_4qYl61ec9-k-2hKc='
    kind = "EdDSA"

    reg["signer"] = signer
    reg["changed"] = nstamp
    reg["keys"].append(ODict(key=nverkey, kind=kind))
    assert reg["keys"][1] == {'key': 'FsSQTQnp_W-6RPkuvULH8h8G5u_4qYl61ec9-k-2hKc=',
                              'kind': 'EdDSA'}
    assert reg['signer'] == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#1"

    nres = json.dumps(reg, indent=2)
    nsig = keyToKey64u(libnacl.crypto_sign(nres.encode("utf-8"), nsk)[:libnacl.crypto_sign_BYTES])
    csig = keyToKey64u(libnacl.crypto_sign(nres.encode("utf-8"), sk)[:libnacl.crypto_sign_BYTES])

    assert nsig == ("Y5xTb0_jTzZYrf5SSEK2f3LSLwIwhOX7GEj6YfRWmGViKAesa08UkNWukUk"
                    "PGuKuu-EAH5U-sdFPPboBAsjRBw==")
    assert csig == ("Xhh6WWGJGgjU5V-e57gj4HcJ87LLOhQr2Sqg5VToTSg-SI1W3A8lgISxOj"
                    "AI5pa2qnonyz3tpGvC2cmf1VTpBg==")

    # now overwrite with new one

    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}";current="{}"'.format(nsig, csig)}

    body = nres  # client.post encodes the body

    didURI = falcon.uri.encode_value(did)
    rep = client.put('/agent/{}'.format(didURI), body=body, headers=headers)
    assert rep.status == falcon.HTTP_200
    assert rep.json == reg
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])
    assert sigs['signer'] == nsig
    assert sigs['signer'] == ('Y5xTb0_jTzZYrf5SSEK2f3LSLwIwhOX7GEj6YfRWmGViKAes'
                              'a08UkNWukUkPGuKuu-EAH5U-sdFPPboBAsjRBw==')
    assert rep.body == (
        '{\n'
        '  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#1",\n'
        '  "changed": "2000-01-02T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '      "kind": "EdDSA"\n'
        '    },\n'
        '    {\n'
        '      "key": "FsSQTQnp_W-6RPkuvULH8h8G5u_4qYl61ec9-k-2hKc=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ]\n'
        '}')

    # verify that its in database

    ddat, dser, dsig = dbing.getSigned(did)

    assert ddat == reg
    assert dser == nres
    assert dsig == nsig

    # now get it

    rep = client.get('/agent/{}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])
    assert sigs['signer'] == nsig
    assert sigs['signer'] == ('Y5xTb0_jTzZYrf5SSEK2f3LSLwIwhOX7GEj6YfRWmGViKAes'
                              'a08UkNWukUkPGuKuu-EAH5U-sdFPPboBAsjRBw==')

    assert rep.body == (
        '{\n'
        '  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#1",\n'
        '  "changed": "2000-01-02T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '      "kind": "EdDSA"\n'
        '    },\n'
        '    {\n'
        '      "key": "FsSQTQnp_W-6RPkuvULH8h8G5u_4qYl61ec9-k-2hKc=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ]\n'
        '}')

    assert rep.json['did'] == did
    assert verify64u(sigs['signer'], rep.body, rep.json['keys'][1]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_put_IssuerDid(client):  # client is a fixture in pytest_falcon
    """
    Test PUT to issuer agent at did.
    Overwrites existing agent data resource with new data
    """
    print("Testing put /agent/{did} for issuer")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    # put an agent into database so we can update it
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
                   b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)

    issuant = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of hid issuants

    sig, res = makeSignedAgentReg(vk, sk, changed=stamp, issuants=issuants)

    reg = json.loads(res, object_pairs_hook=ODict)
    did = reg['did']

    dbing.putSigned(key=did, ser=res, sig=sig, clobber=False)

    vdat, vser, vsig = dbing.getSelfSigned(did)

    assert vdat == reg
    assert vser == res
    assert vsig == sig

    # change signer and key fields
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'Z\xda?\x93M\xf8|\xe2!d\x16{s\x9d\x07\xd2\x98\xf2!\xff\xb8\xb6\xf9Z'
            b'\xe5I\xbc\x97}IFV')

    # creates signing/verification key pair
    nvk, nsk = libnacl.crypto_sign_seed_keypair(seed)

    ndt = datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc)
    nstamp = timing.iso8601(ndt, aware=True)

    index = 1
    signer = "{}#{}".format(did, index)  # signer field value key at index
    nverkey = keyToKey64u(nvk)  # make key index field value
    assert nverkey == '0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI='
    kind = "EdDSA"

    reg["signer"] = signer
    reg["changed"] = nstamp
    reg["keys"].append(ODict(key=nverkey, kind=kind))
    assert reg["keys"][1] == {'key': '0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=',
                              'kind': 'EdDSA'}
    assert reg['signer'] == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1"

    nres = json.dumps(reg, indent=2)

    nsig = keyToKey64u(libnacl.crypto_sign(nres.encode("utf-8"), nsk)[:libnacl.crypto_sign_BYTES])
    csig = keyToKey64u(libnacl.crypto_sign(nres.encode("utf-8"), sk)[:libnacl.crypto_sign_BYTES])

    assert nsig == ("P4CAY5_6Yh1-JbJRPLR11FcvFYcQZKscMeF9tsismbWZmRGSiqNpXcUAiV_zAaBtEOJl99UBR9v30XpGcUSDDw==")
    assert csig == ("yMyy2iEeecI_BtmuAEvLxhUywciPvDn6KHF85KmVuChNr1G3LiOUcxkjmJWNiNkhdcw-0nvFQ60YBCuQbZe_CA==")


    # now overwrite with new one using web service
    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}";current="{}"'.format(nsig, csig)}

    body = nres  # client.post encodes the body

    didURI = falcon.uri.encode_value(did)
    rep = client.put('/agent/{}'.format(didURI), body=body, headers=headers)
    assert rep.status == falcon.HTTP_200
    assert rep.json == reg
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])
    assert sigs['signer'] == nsig
    assert rep.body == (
        '{\n'
        '  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",\n'
        '  "changed": "2000-01-02T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",\n'
        '      "kind": "EdDSA"\n'
        '    },\n'
        '    {\n'
        '      "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ],\n'
        '  "issuants": [\n'
        '    {\n'
        '      "kind": "dns",\n'
        '      "issuer": "generic.com",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "https://generic.com/indigo"\n'
        '    }\n'
        '  ]\n'
        '}')

    # verify that its in database

    vdat, vser, vsig = dbing.getSigned(did)

    assert vdat == reg
    assert vser == nres
    assert vsig == nsig

    # now get it from web service
    rep = client.get('/agent/{}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])
    assert sigs['signer'] == nsig

    assert rep.json['did'] == did
    assert rep.body == nres
    assert verify64u(sigs['signer'], rep.body, rep.json['keys'][1]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_get_ThingDid(client):  # client is a fixture in pytest_falcon
    """
    Test GET to thing at did.
    """
    print("Testing GET /thing/{did}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    # To put thing into database first need to put owning agent and then thing
    # put agent into database
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
            b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)

    asig, aser = makeSignedAgentReg(svk, ssk, changed=stamp)

    adat = json.loads(aser, object_pairs_hook=ODict)
    adid = adat['did']

    dbing.putSigned(key=adid, ser=aser, sig=asig, clobber=False)

    # verify that its in database
    vdat, vser, vsig = dbing.getSigned(adid)

    assert vdat == adat
    assert vser == aser
    assert vsig == asig

    # create thing signed by agent and put into database
    # creates signing/verification key pair thing DID
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
            b'P\xdd&R <\x97\x01')

    dvk, dsk = libnacl.crypto_sign_seed_keypair(seed)

    signer = adat['signer']  # use same signer key fragment reference as agent
    hid = "hid:dns:generic.com#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    dsig, ssig, tser = makeSignedThingReg(dvk,
                                            dsk,
                                            ssk,
                                            signer,
                                            changed=stamp,
                                            hid=hid,
                                            data=data)

    assert ssig == 'bNUB37pBC5KuSVx4SKw8qQGR405wH7qNI2pjv2MhmyqsJ8ofTTS2WYs3ZaU7aDyoJGSIfwJcadmcok9tntdkDA=='

    tdat = json.loads(tser, object_pairs_hook=ODict)
    tdid = tdat['did']

    assert tdid == "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="
    assert tser == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:generic.com#02",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",\n'
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

    dbing.putSigned(key=tdid, ser=tser, sig=ssig, clobber=False)

    # verify that its in database
    vdat, vser, vsig = dbing.getSigned(tdid)

    assert vdat == tdat
    assert vser == tser
    assert vsig == ssig


    # now get it from web service
    didURI = falcon.uri.encode_value(tdid)
    rep = client.get('/thing/{}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.headers['signature'] == ('signer="{}"'.format(ssig))
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == 'bNUB37pBC5KuSVx4SKw8qQGR405wH7qNI2pjv2MhmyqsJ8ofTTS2WYs3ZaU7aDyoJGSIfwJcadmcok9tntdkDA=='

    assert rep.body == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:generic.com#02",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",\n'
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


    assert rep.json['did'] == tdid
    assert verify64u(sigs['signer'], rep.body, adat['keys'][0]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_put_ThingDid(client):  # client is a fixture in pytest_falcon
    """
    Test PUT to thing at did.
    """
    print("Testing PUT /thing/{did}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    # To put thing into database first need to put owning agent and then thing
    # put agent into database
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
            b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)

    issuant = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of hid issuants

    asig, aser = makeSignedAgentReg(svk, ssk, changed=stamp,  issuants=issuants)

    adat = json.loads(aser, object_pairs_hook=ODict)
    adid = adat['did']

    # modify agent so has another key in keys
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'Z\xda?\x93M\xf8|\xe2!d\x16{s\x9d\x07\xd2\x98\xf2!\xff\xb8\xb6\xf9Z'
            b'\xe5I\xbc\x97}IFV')

    # creates signing/verification key pair
    nvk, nsk = libnacl.crypto_sign_seed_keypair(seed)
    nverkey = keyToKey64u(nvk)  # make key index field value
    assert nverkey == '0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI='
    kind = "EdDSA"
    adat["keys"].append(ODict(key=nverkey, kind=kind))
    assert adat["keys"][1] == {'key': '0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=',
                              'kind': 'EdDSA'}

    nser = json.dumps(adat, indent=2)
    # did not change signer so sign with prior signer
    nsig = keyToKey64u(libnacl.crypto_sign(nser.encode("utf-8"), ssk)[:libnacl.crypto_sign_BYTES])
    assert nsig == ('sft7-SsT_n1URyXUPgO76QBw_LXKApxE0x8lv2vcoOaKFWrLSjNrxGGxiKasEgjy0lbw6ZX9O80bZE7dHcJNCg==')

    dbing.putSigned(key=adid, ser=nser, sig=nsig, clobber=False)

    # verify that its in database
    vdat, vser, vsig = dbing.getSelfSigned(adid)

    assert vdat == adat
    assert vser == nser
    assert vsig == nsig

    # create thing signed by agent and put into database
    # creates signing/verification key pair thing DID
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
            b'P\xdd&R <\x97\x01')

    dvk, dsk = libnacl.crypto_sign_seed_keypair(seed)

    signer = adat['signer']  # use same signer key fragment reference as agent
    hid = "hid:dns:generic.com#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    dsig, ssig, tser = makeSignedThingReg(dvk,
                                            dsk,
                                            ssk,
                                            signer,
                                            changed=stamp,
                                            hid=hid,
                                            data=data)

    assert ssig == 'bNUB37pBC5KuSVx4SKw8qQGR405wH7qNI2pjv2MhmyqsJ8ofTTS2WYs3ZaU7aDyoJGSIfwJcadmcok9tntdkDA=='

    tdat = json.loads(tser, object_pairs_hook=ODict)
    tdid = tdat['did']

    assert tdid == "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="
    assert tser == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:generic.com#02",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",\n'
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

    dbing.putSigned(key=tdid, ser=tser, sig=ssig, clobber=False)

    # verify that its in database
    vdat, vser, vsig = dbing.getSigned(tdid)

    assert vdat == tdat
    assert vser == tser
    assert vsig == ssig

    # now change signer field and changed field
    index = 1
    signer = "{}#{}".format(adid, index)  # signer field value key at index
    assert signer == 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1'
    tdat['signer'] = signer

    dt = datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    tdat['changed'] = stamp

    # now double sign and put to web service
    ntser = json.dumps(tdat, indent=2)

    ntsig = keyToKey64u(libnacl.crypto_sign(ntser.encode("utf-8"), nsk)[:libnacl.crypto_sign_BYTES])
    ctsig = keyToKey64u(libnacl.crypto_sign(ntser.encode("utf-8"), ssk)[:libnacl.crypto_sign_BYTES])

    assert ntsig == ("5SwnZroMIcOpx1vEYkcSajnU3BhrqBpovq0NnCwL43kuEs-GTfwd6bpQJ_L5bMhfRAZZEgkjVqFx4HCGGLc9DA==")
    assert ctsig == ("3GhKWYXFL0JGTnhK3vB0087Rib4nhjfts12KjJMr5EOa2AO6uqyBZyziKVfa7WUK5mvFPyo-Hxjx4GPTV5AGBw==")

    # now overwrite with new one using web service
    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}";current="{}"'.format(ntsig, ctsig)}
    body = ntser  # client.post encodes the body
    didURI = falcon.uri.encode_value(tdid)
    rep = client.put('/thing/{}'.format(didURI), body=body, headers=headers)
    assert rep.status == falcon.HTTP_200
    assert rep.json == tdat
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])
    assert sigs['signer'] == ntsig
    assert rep.body == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:generic.com#02",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",\n'
        '  "changed": "2000-01-02T00:00:00+00:00",\n'
        '  "data": {\n'
        '    "keywords": [\n'
        '      "Canon",\n'
        '      "EOS Rebel T6",\n'
        '      "251440"\n'
        '    ],\n'
        '    "message": "If found please return."\n'
        '  }\n'
        '}')

    # verify that its in database

    vdat, vser, vsig = dbing.getSigned(tdid)

    assert vdat == tdat
    assert vser == ntser
    assert vsig == ntsig

    # now get it from web service
    didURI = falcon.uri.encode_value(tdid)
    rep = client.get('/thing/{}'.format(didURI))

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == ntsig

    assert rep.body == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:generic.com#02",\n'
        '  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",\n'
        '  "changed": "2000-01-02T00:00:00+00:00",\n'
        '  "data": {\n'
        '    "keywords": [\n'
        '      "Canon",\n'
        '      "EOS Rebel T6",\n'
        '      "251440"\n'
        '    ],\n'
        '    "message": "If found please return."\n'
        '  }\n'
        '}')


    assert rep.json['did'] == tdid
    assert verify64u(sigs['signer'], rep.body, adat['keys'][1]['key'])

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_post_AgentDidDrop(client):  # client is a fixture in pytest_falcon
    """
    Test POST drop message to agent .

    {
        "uid": "m_00035d2976e6a000_26ace93",
        "kind": "found",
        "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
        "date": "2000-01-03T00:00:00+00:00",
        "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
        "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
        "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
        "subject": "Lose something?",
        "content": "Look what I found"
    }
    """
    print("Testing POST /agent/{adid}/drop")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    for did, vk, sk in agents.values():
        dat, ser, sig = dbing.getSelfSigned(did)
        assert dat is not None
        assert dat['did'] == did

    for did, vk, sk in things.values():
        dat, ser, sig = dbing.getSigned(did)
        assert dat is not None
        assert dat['did'] == did

    # post message from Ann to Ivy
    dt = datetime.datetime(2000, 1, 3, tzinfo=datetime.timezone.utc)
    changed = timing.iso8601(dt, aware=True)
    assert changed == "2000-01-03T00:00:00+00:00"

    stamp = dt.timestamp()  # make time.time value
    #muid = timing.tuuid(stamp=stamp, prefix="m")
    muid = "m_00035d2976e6a000_26ace93"
    assert muid == "m_00035d2976e6a000_26ace93"

    srcDid, srcVk, srcSk = agents['ann']
    dstDid, dstVk, dskSk = agents['ivy']
    thingDid, thingVk, thingSk = things['cam']

    assert dstDid == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="

    signer = "{}#0".format(srcDid)
    assert signer == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"

    msg = ODict()
    msg['uid'] = muid
    msg['kind'] = "found"
    msg['signer'] = "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"
    msg['date'] = changed
    msg['to'] = dstDid
    msg['from'] = srcDid
    msg['thing'] = thingDid
    msg['subject'] = "Lose something?"
    msg['content'] = "Look what I found"

    mser = json.dumps(msg, indent=2)
    msig = keyToKey64u(libnacl.crypto_sign(mser.encode("utf-8"), srcSk)[:libnacl.crypto_sign_BYTES])
    assert msig == "07u1OcQI8FUeWPqeiga3A9k4MPJGSFmC4vShiJNpv2Rke9ssnW7aLx857HC5ZaJ973WSKkLAwPzkl399d01HBA=="

    dstDidUri = falcon.uri.encode_value(dstDid)
    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(msig)}
    body = mser  # client.post encodes the body
    rep = client.post('/agent/{}/drop'.format(dstDidUri),
                      body=body,
                      headers=headers)

    assert rep.status == falcon.HTTP_201
    assert msg == rep.json
    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/agent/{}/drop?from={}&uid={}".format(dstDid, srcDid, muid)

    # now get it from web service
    # need to use uri encode version of location header
    assert rep.headers['location'] == ('/agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ'
                                       '9GroAvxqFi2RTZWlkC0raY%3D/drop'
                                       '?from=did%3Aigo%3AQt27fThWoNZsa88VrTkep'
                                       '6H-4HA8tr54sHON1vWl6FE%3D&'
                                       'uid=m_00035d2976e6a000_26ace93')
    rep = client.get(rep.headers['location'])

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == msig

    assert rep.body == (
        '{\n'
        '  "uid": "m_00035d2976e6a000_26ace93",\n'
        '  "kind": "found",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",\n'
        '  "date": "2000-01-03T00:00:00+00:00",\n'
        '  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",\n'
        '  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "subject": "Lose something?",\n'
        '  "content": "Look what I found"\n'
        '}')

    assert verify64u(msig, rep.body, keyToKey64u(srcVk))

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_get_AgentDidDrop(client):  # client is a fixture in pytest_falcon
    """
    Test GET drop message to agent

    {
        "uid": "m_00035d2976e6a000_26ace93",
        "kind": "found",
        "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
        "date": "2000-01-03T00:00:00+00:00",
        "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
        "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
        "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
        "subject": "Lose something?",
        "content": "Look what I found"
    }
    """
    print("Testing GET /agent/{adid}/drop/{cdid}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    for did, vk, sk in agents.values():
        dat, ser, sig = dbing.getSelfSigned(did)
        assert dat is not None
        assert dat['did'] == did

    for did, vk, sk in things.values():
        dat, ser, sig = dbing.getSigned(did)
        assert dat is not None
        assert dat['did'] == did

    # Insert message from Ann to Ivy into database
    dt = datetime.datetime(2000, 1, 3, tzinfo=datetime.timezone.utc)
    changed = timing.iso8601(dt, aware=True)
    assert changed == "2000-01-03T00:00:00+00:00"

    stamp = dt.timestamp()  # make time.time value
    #muid = timing.tuuid(stamp=stamp, prefix="m")
    muid = "m_00035d2976e6a000_26ace93"
    assert muid == "m_00035d2976e6a000_26ace93"

    srcDid, srcVk, srcSk = agents['ann']
    dstDid, dstVk, dskSk = agents['ivy']
    thingDid, thingVk, thingSk = things['cam']

    signer = "{}#0".format(srcDid)
    assert signer == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"

    msg = ODict()
    msg['uid'] = muid
    msg['kind'] = "found"
    msg['signer'] = "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"
    msg['date'] = changed
    msg['to'] = dstDid
    msg['from'] = srcDid
    msg['thing'] = thingDid
    msg['subject'] = "Lose something?"
    msg['content'] = "Look what I found"

    mser = json.dumps(msg, indent=2)
    msig = keyToKey64u(libnacl.crypto_sign(mser.encode("utf-8"), srcSk)[:libnacl.crypto_sign_BYTES])

    key = "{}/drop/{}/{}".format(dstDid, srcDid, muid)
    assert key == ("did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="
                   "/drop/did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="
                   "/m_00035d2976e6a000_26ace93")
    dbing.putSigned(key=key, ser=mser, sig=msig)

    # now get it from web service
    dstDidUri = falcon.uri.encode_value(dstDid)
    srcDidUri = falcon.uri.encode_value(srcDid)
    rep = client.get("/agent/{}/drop?from={}&uid={}".format(dstDidUri, srcDidUri, muid))

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])

    assert sigs['signer'] == msig

    assert rep.body == (
        '{\n'
        '  "uid": "m_00035d2976e6a000_26ace93",\n'
        '  "kind": "found",\n'
        '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",\n'
        '  "date": "2000-01-03T00:00:00+00:00",\n'
        '  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",\n'
        '  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "subject": "Lose something?",\n'
        '  "content": "Look what I found"\n'
        '}')

    assert verify64u(msig, rep.body, keyToKey64u(srcVk))

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_post_ThingDidOffer(client):  # client is a fixture in pytest_falcon
    """
    Test POST offer of thing.

    offer request fields
    {
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
    }

    offer response fields
    {
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
        "expiration": datetimeofexpiration,
        "signer": serverkeydid,
        "offerer": ownerkeydid,
        "offer": Base64serrequest
    }
    """
    print("Testing POST /thing/{did}/offer")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    for did, vk, sk in agents.values():
        dat, ser, sig = dbing.getSelfSigned(did)
        assert dat is not None
        assert dat['did'] == did

    for did, vk, sk in things.values():
        dat, ser, sig = dbing.getSigned(did)
        assert dat is not None
        assert dat['did'] == did

    setupTestPriorOffer(agents=agents, things=things, ago=600.0)  # to test that it checks for priors

    sDid, sVk, sSk = agents['sam']  # server keys

    # post offer Ivy to Ann
    hDid, hVk, hSk = agents['ivy']
    aDid, aVk, aSk = agents['ann']

    tDid, tVk, tSk = things['cam']

    assert tDid == "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="

    signer = "{}#0".format(hDid)
    assert signer == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0"

    #dt = datetime.datetime(2000, 1, 3, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    #ouid = timing.tuuid(stamp=stamp, prefix="o")
    ouid = "o_00035d2976e6a000_26ace93"

    offer = ODict()
    offer['uid'] = ouid
    offer['thing'] = tDid
    offer['aspirant'] = aDid
    offer['duration'] = PROPAGATION_DELAY * 2.0
    oser = json.dumps(offer, indent=2)
    assert oser == (
        '{\n'
        '  "uid": "o_00035d2976e6a000_26ace93",\n'
        '  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
        '  "duration": 120.0\n'
        '}')
    osig = keyToKey64u(libnacl.crypto_sign(oser.encode("utf-8"), hSk)[:libnacl.crypto_sign_BYTES])
    assert osig == 'EhsfS2_4LSVjDMo_QShvciNr6aYf5ut8NuFkBugxL748vlOs1YF971aPIckmtRRAFzby07hY0Ny-7xs27-wXCw=='

    dt = datetime.datetime.now(tz=datetime.timezone.utc)

    tDidUri = falcon.uri.encode_value(tDid)
    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(osig)}
    body = oser  # client.post encodes the body
    rep = client.post('/thing/{}/offer'.format(tDidUri),
                      body=body,
                      headers=headers)

    assert rep.status == falcon.HTTP_201
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/thing/{}/offer?uid={}".format(tDid, ouid)

    expiration = rep.json['expiration']
    edt = arrow.get(expiration)
    assert edt > dt
    offer = rep.json
    offser = rep.body
    assert offer['offerer'].startswith(hDid)
    assert offer['signer'].startswith(sDid)

    # now get it from web service
    rep = client.get(rep.headers['location'])

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'

    sigs = parseSignatureHeader(rep.headers['signature'])
    ssig = sigs['signer']  # signature changes everytime because expiration changes

    assert rep.json == offer
    assert rep.body == offser

    assert verify64u(ssig, rep.body, keyToKey64u(sVk))

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_get_ThingDidOffer(client):  # client is a fixture in pytest_falcon
    """
    Test GET offer of thing.

    offer request fields
    {
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
    }

    offer response fields
    {
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
        "expiration": datetimeofexpiration,
        "signer": serverkeydid,
        "offerer": ownerkeydid,
        "offer": Base64serrequest
    }
    """
    print("Testing GET /thing/{did}/offer?uid=")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    for did, vk, sk in agents.values():
        dat, ser, sig = dbing.getSelfSigned(did)
        assert dat is not None
        assert dat['did'] == did

    for did, vk, sk in things.values():
        dat, ser, sig = dbing.getSigned(did)
        assert dat is not None
        assert dat['did'] == did

    sDid, sVk, sSk = agents['sam']  # server keys

    # post offer Ivy to Ann
    hDid, hVk, hSk = agents['ivy']
    aDid, aVk, aSk = agents['ann']

    tDid, tVk, tSk = things['cam']

    #dt = datetime.datetime(2000, 1, 3, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    #ouid = timing.tuuid(stamp=stamp, prefix="o")
    ouid = "o_00035d2976e6a000_26ace93"

    duration = PROPAGATION_DELAY * 2.0
    offerer = "{}#0".format(hDid)  # ivy is offerer

    # build prior request offer for saved offer
    poffer = ODict()
    poffer['uid'] = ouid
    poffer['thing'] = tDid
    poffer['aspirant'] = aDid
    poffer['duration'] = duration
    poser = json.dumps(poffer, indent=2)

    # now build offer in database
    odat = ODict()
    odat['uid'] = ouid
    odat['thing'] = tDid
    odat['aspirant'] = aDid
    odat['duration'] = duration

    dt = datetime.datetime.now(tz=datetime.timezone.utc)
    # go back 10 minutes
    td = datetime.timedelta(seconds=10 * 60)
    odt = dt - td

    td = datetime.timedelta(seconds=duration)
    expiration = timing.iso8601(odt + td, aware=True)
    odat["expiration"] = expiration

    signer = "{}#0".format(sDid)  # server sam signs
    assert signer == "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0"
    odat["signer"] = signer
    odat["offerer"] = offerer
    odat["offer"] = keyToKey64u(poser.encode("utf-8"))

    oser = json.dumps(odat, indent=2)
    osig = keyToKey64u(libnacl.crypto_sign(oser.encode("utf-8"), sSk)[:libnacl.crypto_sign_BYTES])

    key = "{}/offer/{}".format(tDid, ouid)

    # save offer to database, raise error if duplicate
    dbing.putSigned(key=key, ser=oser, sig=osig, clobber=False)  # no clobber so error

    # save entry to offer expires table
    result = dbing.putDidOfferExpire(did=tDid,
                                         ouid=ouid,
                                         expire=expiration)
    # now get it from web service
    tDidUri = falcon.uri.encode_value(tDid)
    location = "/thing/{}/offer?uid={}".format(tDidUri, ouid)
    rep = client.get(location)

    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'

    sigs = parseSignatureHeader(rep.headers['signature'])
    ssig = sigs['signer']  # signature changes everytime because expiration changes

    assert rep.json == odat
    assert rep.body == oser

    assert verify64u(ssig, rep.body, keyToKey64u(sVk))

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def setupTestPriorOffer(agents, things, ago=600.0):
    """
    Utility function to create prior offer in database at ago seconds
    in the past.

    Agents and things are ODicts of Agents and things in database

    offer request fields
    {
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
    }

    offer response fields
    {
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
        "expiration": datetimeofexpiration,
        "signer": serverkeydid,
        "offerer": ownerkeydid,
        "offer": Base64serrequest
    }
    """
    # Assumes database setup
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper

    sDid, sVk, sSk = agents['sam']  # server keys

    # post offer Ivy to Ann to transfer cam
    hDid, hVk, hSk = agents['ivy']
    aDid, aVk, aSk = agents['ann']
    tDid, tVk, tSk = things['cam']

    dt = datetime.datetime.now(tz=datetime.timezone.utc)
    # go back ago seconds
    td = datetime.timedelta(seconds=ago)
    odt = dt - td

    stamp = odt.timestamp()  # make time.time value
    ouid = timing.tuuid(stamp=stamp, prefix="o")

    duration = PROPAGATION_DELAY * 2.0
    offerer = "{}#0".format(hDid)  # ivy is offerer

    # build prior request offer for saved offer
    poffer = ODict()
    poffer['uid'] = ouid
    poffer['thing'] = tDid
    poffer['aspirant'] = aDid
    poffer['duration'] = duration
    poser = json.dumps(poffer, indent=2)

    # now build offer in database
    odat = ODict()
    odat['uid'] = ouid
    odat['thing'] = tDid
    odat['aspirant'] = aDid
    odat['duration'] = duration

    td = datetime.timedelta(seconds=duration)
    expiration = timing.iso8601(odt + td, aware=True)
    odat["expiration"] = expiration

    signer = "{}#0".format(sDid)  # server sam signs
    odat["signer"] = signer
    odat["offerer"] = offerer
    odat["offer"] = keyToKey64u(poser.encode("utf-8"))

    oser = json.dumps(odat, indent=2)
    osig = keyToKey64u(libnacl.crypto_sign(oser.encode("utf-8"), sSk)[:libnacl.crypto_sign_BYTES])

    key = "{}/offer/{}".format(tDid, ouid)

    # save offer to database, raise error if duplicate
    dbing.putSigned(key=key, ser=oser, sig=osig, clobber=False)  # no clobber so error

    # save entry to offer expires table
    result = dbing.putDidOfferExpire(did=tDid,
                                         ouid=ouid,
                                         expire=expiration)

    return (tDid, ouid)


def test_post_ThingDidAccept(client):  # client is a fixture in pytest_falcon
    """
    Test POST  to thing/did/accept with parameter offer uid.
    """
    print("Testing POST /thing/{did}/accept?uid={ouid}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    for did, vk, sk in agents.values():
        dat, ser, sig = dbing.getSelfSigned(did)
        assert dat is not None
        assert dat['did'] == did

    for did, vk, sk in things.values():
        dat, ser, sig = dbing.getSigned(did)
        assert dat is not None
        assert dat['did'] == did

    sDid, sVk, sSk = agents['sam']  # server keys

    # post offer Ivy to Ann
    hDid, hVk, hSk = agents['ivy']
    aDid, aVk, aSk = agents['ann']

    tDid, tVk, tSk = things['cam']

    odid, ouid = setupTestPriorOffer(agents=agents, things=things, ago=10.0)  # to test that it checks for priors

    assert odid == tDid

    # We now have thing in database with offer from ivy to ann
    # get think resource and change it to have ann as signer
    tdat, tser, tsig = dbing.getSigned(tDid)

    # now change signer field  to ann as signer
    index = 0
    signer = "{}#{}".format(aDid, index)  # signer field value key at index
    assert signer == 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0'
    tdat['signer'] = signer

    # now sign and post to accept
    atser = json.dumps(tdat, indent=2)
    assert atser == (
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

    atsig = keyToKey64u(libnacl.crypto_sign(atser.encode("utf-8"), aSk)[:libnacl.crypto_sign_BYTES])
    assert atsig == "RtlBu9sZgqhfc0QbGe7IHqwsHOARrGNjy4BKJG7gNfNP4GfKDQ8FGdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg=="

    # now accept offer with new thing resource using web service
    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": 'signer="{}"'.format(atsig)}
    body = atser  # client.post encodes the body
    tDidUri = falcon.uri.encode_value(tDid)
    rep = client.post('/thing/{}/accept?uid={}'.format(tDidUri, ouid),
                      body=body,
                      headers=headers)

    assert rep.status == falcon.HTTP_201
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/thing/{}".format(tDid)
    assert rep.json == tdat

    # verify that its in database
    vdat, vser, vsig = dbing.getSigned(tDid)

    assert vdat == tdat
    assert vser == atser
    assert vsig == atsig

    # now get it from web service
    rep = client.get(rep.headers['location'])
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    sigs = parseSignatureHeader(rep.headers['signature'])
    ssig = sigs['signer']  # signature changes everytime because expiration changes

    assert rep.json == tdat
    assert rep.body == atser

    assert verify64u(ssig, rep.body, keyToKey64u(aVk))

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_post_Track(client):  # client is a fixture in pytest_falcon
    """
    Test POST  to thing/did/accept with parameter offer uid.

    eid is track ephemeral ID in hex lowercase
    loc is location string in hex lowercase
    dts is iso8601 datetime stamp

    The value of the entry is serialized JSON
    {
        create: 1501774813367861, # creation in server time microseconds since epoch
        expire: 1501818013367861, # expiration in server time microseconds since epoch
        track:
        {
            eid: "abcdef0123456789,  # lower case 16 char hex of 8 byte eid
            loc: "1111222233334444", # lower case 16 char hex of 8 byte location
            dts: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of track gateway time
        }
    }
    """
    print("Testing POST /thing/{did}/accept?uid={ouid}")

    priming.setupTest()
    dbEnv = dbing.gDbEnv

    dt = datetime.datetime(2000, 1, 1, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value

    # local time
    td = datetime.timedelta(seconds=5)
    dts = timing.iso8601(dt=dt+td, aware=True)
    assert dts == '2000-01-01T00:30:05+00:00'

    eid = "010203040a0b0c0d"
    loc = "1234567812345678"

    track = ODict()
    track['eid'] = eid
    track['loc'] = loc
    track['dts'] = dts

    assert track == {
        "eid": "010203040a0b0c0d",
        "loc": "1234567812345678",
        "dts": "2000-01-01T00:30:05+00:00",
    }

    tser = json.dumps(track, indent=2)

    # now post track
    headers = {"Content-Type": "text/html; charset=utf-8"}
    body = tser  # client.post encodes the body
    rep = client.post('/track',
                      body=body,
                      headers=headers)

    assert rep.status == falcon.HTTP_201
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    location = falcon.uri.decode(rep.headers['location'])
    assert location == "/track?eid={}".format(eid)
    data = rep.json
    assert data['track'] == track

    create = rep.json['create']
    expire = rep.json['expire']
    assert expire > create


    # verify that track is in database
    entries = dbing.getTracks(eid)
    assert entries[0] == data

    #verify expiration in its database
    entries = dbing.getExpireEid(expire)
    assert entries[0] == eid

    # now get it from web service
    rep = client.get(rep.headers['location'])
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'

    assert rep.json[0] == data

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")
