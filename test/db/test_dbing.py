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
from bluepea.help.helping import (keyToKey64u,
                                  setupTmpBaseDir, cleanupTmpBaseDir,
                                  makeSignedAgentReg, makeSignedThingReg)

from bluepea.db import dbing
from bluepea.prime import priming
from bluepea.keep import keeping


def test_setupDbEnv():
    """

    """
    print("Testing Setup DB Env")

    baseDirPath = setupTmpBaseDir()
    assert baseDirPath.startswith("/tmp/bluepea")
    assert baseDirPath.endswith("test")
    dbDirPath = os.path.join(baseDirPath, "bluepea/db")
    os.makedirs(dbDirPath)
    assert os.path.exists(dbDirPath)

    env = dbing.setupDbEnv(baseDirPath=dbDirPath)
    assert env.path() == dbDirPath

    assert dbing.gDbDirPath == dbDirPath
    assert dbing.gDbEnv is env

    data = ODict()

    dbCore = dbing.gDbEnv.open_db(b'core')  # open named sub db named 'core' within env

    with dbing.gDbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
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
    print("Testing putSigned and getSelfSigned")

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
    dbing.putSigned(key=did, ser=ser, sig=sig, clobber=False)

    gdat, gser, gsig = dbing.getSelfSigned(did)
    assert gdat == dat
    assert gser == ser
    assert gsig == sig

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_putSigned_getSigned():
    """
    Test putSigned and getSigned
    """
    print("Testing putSigned and getSigned")

    dbEnv = dbing.setupTestDbEnv()

    # Create self signed resource
    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    issuant = ODict(kind="dns",
                     issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of issuants of hid name spaces

    ssig, sser = makeSignedAgentReg(svk,
                                    ssk,
                                    changed=stamp,
                                    issuants=issuants)

    assert len(ssig) == 88
    assert ssig == ('Fgn0uNoZ4OqJrqiKv03HotWztrrM2ZPapf-977nZEtlpk6JPywuFFem6f4UZOZkNcvAbfUalwAr29nkX5P6ADg==')

    assert len(sser) == 477
    assert SEPARATOR not in sser  # separator
    assert sser == (
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
        '  "issuants": [\n'
        '    {\n'
        '      "kind": "dns",\n'
        '      "issuer": "generic.com",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "https://generic.com/indigo"\n'
        '    }\n'
        '  ]\n'
        '}')

    sdat = json.loads(sser, object_pairs_hook=ODict)
    sdid = sdat['did']
    assert sdid == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="
    dbing.putSigned(key=sdid, ser=sser, sig=ssig, clobber=False)

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


    signer = sdat['signer']
    assert signer == 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0'
    hid = "hid:dns:generic.com#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    dsig, tsig, tser = makeSignedThingReg(dvk,
                                            dsk,
                                            ssk,
                                            signer,
                                            changed=stamp,
                                            hid=hid,
                                            data=data)


    assert tser == (
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

    assert dsig == ('kWZwPfepoAV9zyt9B9vPlPNGeb_POHlP9LL3H-PH71WWZzVJT1Ce'
                          '64IKj1GmOXkNo2JaXrnIpQyfm2vynn7mCg==')

    assert tsig == ('RtlBu9sZgqhfc0QbGe7IHqwsHOARrGNjy4BKJG7gNfNP4GfKDQ8F'
                          'Gdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg==')

    tdat = json.loads(tser, object_pairs_hook=ODict)
    tdid = tdat['did']
    assert tdid == "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="
    dbing.putSigned(key=tdid, ser=tser, sig=tsig, clobber=False)

    gdat, gser, gsig = dbing.getSigned(tdid)
    assert gdat == tdat
    assert gser == tser
    assert gsig == tsig

    dbing.putHid(hid, tdid)
    # verify hid table entry
    dbHid2Did = dbEnv.open_db(b'hid2did')  # open named sub db named 'hid2did' within env
    with dbEnv.begin(db=dbHid2Did) as txn:  # txn is a Transaction object
        tdidb = txn.get(hid.encode("utf-8"))  # keys are bytes

    assert tdidb.decode("utf-8") == tdid

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_exists():
    """

    """
    print("Testing exits in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    data = ODict()
    data["name"] = "John Smith"
    data["city"] = "Alta"
    datab = json.dumps(data, indent=2).encode("utf-8")

    dbCore = dbing.gDbEnv.open_db(b'core')  # open named sub db named 'core' within env
    with dbing.gDbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
        txn.put(b'person0', datab)  # keys and values are bytes
        d0b = txn.get(b'person0')
        assert d0b == datab

    result = dbing.exists(key="person0")
    assert result is True
    result = dbing.exists(key="person1")
    assert result is False

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_getEntities():
    """
    Test get all entities Agents and Things in db

    getEntities(dbn='core', env=None)
    """
    print("Testing getEntities in DB Env")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = dbing.setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    entities = dbing.getEntities()
    assert len(entities) == 6
    assert entities == [ODict([('did', 'did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA='),
                                     ('kind', 'agent')]),
                        ODict([('did', 'did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM='),
                                     ('kind', 'thing')]),
                        ODict([('did', 'did:igo:QBRKvLW1CnVDIgznfet3rpad-wZBL4qGASVpGRsE2uU='),
                                     ('kind', 'agent')]),
                        ODict([('did', 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='),
                                     ('kind', 'agent')]),
                        ODict([('did', 'did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148='),
                                     ('kind', 'agent')]),
                        ODict([('did', 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY='),
                                     ('kind', 'agent')])]


    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_getAgents():
    """
    Test get all Agents in db

    getEntities(dbn='core', env=None)
    """
    print("Testing getAgents in DB Env")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = dbing.setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    entries = dbing.getAgents()
    assert len(entries) == 5
    assert entries == ['did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=',
                    'did:igo:QBRKvLW1CnVDIgznfet3rpad-wZBL4qGASVpGRsE2uU=',
                    'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
                    'did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=',
                    'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=']

    entries = dbing.getAgents(issuer=True)
    assert len(entries) == 3
    assert entries == ['did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=',
                        'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
                        'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=']


    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_getThings():
    """
    Test get all Things in db

    getEntities(dbn='core', env=None)
    """
    print("Testing getThings in DB Env")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = dbing.setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    entries = dbing.getThings()
    assert len(entries) == 1
    assert entries == ['did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=']

    did = dbing.getHid(key="hid:dns:localhost#02")
    assert did == entries[0]

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_getDrops():
    """
    Test get essage drop entries in core database for a given did

    getDrops(did, dbn='core', env=None)
    """
    print("Testing getDrops in DB Env")

    priming.setupTest()
    dbEnv = dbing.gDbEnv
    keeper = keeping.gKeeper
    kdid = keeper.did

    agents, things = dbing.setupTestDbAgentsThings()
    agents['sam'] = (kdid, keeper.verkey, keeper.sigkey)  # sam the server

    for did, vk, sk in agents.values():
        dat, ser, sig = dbing.getSelfSigned(did)
        assert dat is not None
        assert dat['did'] == did

    for did, vk, sk in things.values():
        dat, ser, sig = dbing.getSigned(did)
        assert dat is not None
        assert dat['did'] == did

    annDid, annVk, annSk = agents['ann']
    ivyDid, ivyVk, ivySk = agents['ivy']
    thingDid, thingVk, thingSk = things['cam']

    assert annDid == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="
    assert ivyDid == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="

    # test empty inbox for ivy
    messages = dbing.getDrops(ivyDid)
    assert not messages

    # test empty inbox for ann
    messages = dbing.getDrops(annDid)
    assert not messages

    # create message from Ann to Ivy
    dt = datetime.datetime(2000, 1, 3, tzinfo=datetime.timezone.utc)
    changed = timing.iso8601(dt, aware=True)
    assert changed == "2000-01-03T00:00:00+00:00"

    stamp = dt.timestamp()  # make time.time value
    #muid = timing.tuuid(stamp=stamp, prefix="m")
    muid = "m_00035d2976e6a000_26ace93"
    assert muid == "m_00035d2976e6a000_26ace93"

    signer = "{}#0".format(annDid)
    assert signer == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"

    msg = ODict()
    msg['uid'] = muid
    msg['kind'] = "found"
    msg['signer'] = signer
    msg['date'] = changed
    msg['to'] = ivyDid
    msg['from'] = annDid
    msg['thing'] = thingDid
    msg['subject'] = "Lose something?"
    msg['content'] = "Look what I found"

    mser = json.dumps(msg, indent=2)
    msig = keyToKey64u(libnacl.crypto_sign(mser.encode("utf-8"), annSk)[:libnacl.crypto_sign_BYTES])
    assert msig == "07u1OcQI8FUeWPqeiga3A9k4MPJGSFmC4vShiJNpv2Rke9ssnW7aLx857HC5ZaJ973WSKkLAwPzkl399d01HBA=="

    # Build key for message from (to, from, uid)  (did, sdid, muid)
    key = "{}/drop/{}/{}".format(ivyDid, annDid, muid)
    assert key == ('did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY='
                   '/drop'
                   '/did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='
                   '/m_00035d2976e6a000_26ace93')

    # save message to database error if duplicate
    dbing.putSigned(key=key, ser=mser, sig=msig, clobber=False)  # no clobber so error

    #test get inbox for Ivy
    messages = dbing.getDrops(ivyDid)
    assert messages
    assert len(messages) == 1
    assert messages[0]['uid'] == muid
    assert messages[0]['from'] == annDid

    # create another message from Ann to Ivy
    dt = datetime.datetime(2000, 1, 4, tzinfo=datetime.timezone.utc)
    changed = timing.iso8601(dt, aware=True)
    assert changed == "2000-01-04T00:00:00+00:00"

    stamp = dt.timestamp()  # make time.time value
    #muid = timing.tuuid(stamp=stamp, prefix="m")
    muid = "m_00035d3d94be0000_15aabb5"
    assert muid == "m_00035d3d94be0000_15aabb5"

    signer = "{}#0".format(annDid)
    assert signer == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"

    msg = ODict()
    msg['uid'] = muid
    msg['kind'] = "found"
    msg['signer'] = signer
    msg['date'] = changed
    msg['to'] = ivyDid
    msg['from'] = annDid
    msg['thing'] = thingDid
    msg['subject'] = "Lose something?"
    msg['content'] = "Look what I found again"

    mser = json.dumps(msg, indent=2)
    msig = keyToKey64u(libnacl.crypto_sign(mser.encode("utf-8"), annSk)[:libnacl.crypto_sign_BYTES])
    assert msig == "HgFcqSGI20okVh3K611XvEAsHHiV9yXDnFvd0djlZyA52K09E4BZbCnJ2Ejd8yFfRFc1GcTblbUYpDVwpumgCQ=="

    # Build key for message from (to, from, uid)  (did, sdid, muid)
    key = "{}/drop/{}/{}".format(ivyDid, annDid, muid)
    assert key == ('did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY='
                   '/drop'
                   '/did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='
                   '/m_00035d3d94be0000_15aabb5')

    # save message to database error if duplicate
    dbing.putSigned(key=key, ser=mser, sig=msig, clobber=False)  # no clobber so error

    #test get inbox for Ivy
    messages = dbing.getDrops(ivyDid)
    assert messages
    assert len(messages) == 2
    assert messages[1]['uid'] == muid
    assert messages[1]['from'] == annDid

    # create message from Ivy to Ann
    dt = datetime.datetime(2000, 1, 4, tzinfo=datetime.timezone.utc)
    changed = timing.iso8601(dt, aware=True)
    assert changed == "2000-01-04T00:00:00+00:00"

    stamp = dt.timestamp()  # make time.time value
    #muid = timing.tuuid(stamp=stamp, prefix="m")
    muid = "m_00035d3d94be0000_15aabb5"  # use duplicate muid to test no collision
    assert muid == "m_00035d3d94be0000_15aabb5"

    signer = "{}#0".format(ivyDid)
    assert signer == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0"

    msg = ODict()
    msg['uid'] = muid
    msg['kind'] = "found"
    msg['signer'] = signer
    msg['date'] = changed
    msg['to'] = annDid
    msg['from'] = ivyDid
    msg['thing'] = thingDid
    msg['subject'] = "Lose something?"
    msg['content'] = "I am so happy your found it."

    mser = json.dumps(msg, indent=2)
    msig = keyToKey64u(libnacl.crypto_sign(mser.encode("utf-8"), annSk)[:libnacl.crypto_sign_BYTES])
    assert msig == "62ThJr_GUImtTa54RVhbo1bs5X4DCxjmecHONniQp0Os95Pb8bLrzBgCYr3YOhSB8wMPHYL7L6pm5qQjVPYzAA=="

    # Build key for message from (to, from, uid)  (did, sdid, muid)
    key = "{}/drop/{}/{}".format(annDid, ivyDid, muid)
    assert key == ('did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='
                   '/drop'
                   '/did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY='
                   '/m_00035d3d94be0000_15aabb5')

    # save message to database error if duplicate
    dbing.putSigned(key=key, ser=mser, sig=msig, clobber=False)  # no clobber so error

    #test get inbox for Ann
    messages = dbing.getDrops(annDid)
    assert messages
    assert len(messages) == 1
    assert messages[0]['uid'] == muid
    assert messages[0]['from'] == ivyDid

    #test get inbox for Ivy to make sure still works
    messages = dbing.getDrops(ivyDid)
    assert messages
    assert len(messages) == 2
    for message in messages:
        assert message['from'] == annDid


    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_putOfferExpire():
    """
    Test put entry in did2offer database

    putOfferExpire(expire, did, ouid, dbn="did2offer", env=None)
    """
    print("Testing putOfferExpire in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 1, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    #ouid = timing.tuuid(stamp=stamp, prefix="o")
    ouid = "o_00035d2976e6a000_26ace93"

    did = "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="
    expire = timing.iso8601(dt=dt, aware=True)
    assert expire == "2000-01-01T00:30:00+00:00"

    result = dbing.putDidOfferExpire(did, ouid, expire)
    assert result

    # verify in database
    assert dbing.exists(did, dbn='did2offer', dup=True) == True

    # read from database
    subDb = dbing.gDbEnv.open_db(b"did2offer", dupsort=True)  # open named sub db named dbn within env
    with dbing.gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        rsrcb = txn.get(did.encode("utf-8"))

    rsrc = rsrcb.decode("utf-8")
    assert rsrc == (
        '{\n'
        '  "offer": '
        '"did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=/offer/o_00035d2976e6a000_26ace93",\n'
        '  "expire": "2000-01-01T00:30:00+00:00"\n'
        '}')

    dat = json.loads(rsrc, object_pairs_hook=ODict)

    offer = "{}/offer/{}".format(did, ouid)
    assert offer == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=/offer/o_00035d2976e6a000_26ace93"

    assert dat["offer"] == offer
    assert dat["expire"] == expire

    # write another one
    td = datetime.timedelta(seconds=360)
    expire1 = timing.iso8601(dt=dt+td, aware=True)
    assert expire1 == "2000-01-01T00:36:00+00:00"

    result = dbing.putDidOfferExpire(did, ouid, expire1)
    assert result == {
        'offer': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=/offer/o_00035d2976e6a000_26ace93',
        'expire': '2000-01-01T00:36:00+00:00',
        }

    # read from database
    entries = []
    subDb = dbing.gDbEnv.open_db(b"did2offer", dupsort=True)  # open named sub db named dbn within env
    with dbing.gDbEnv.begin(db=subDb) as txn:  # txn is a Transaction object
        with txn.cursor() as cursor:
            if cursor.set_key(did.encode("utf-8")):
                entries = [json.loads(value.decode("utf-8"), object_pairs_hook=ODict)
                           for value in cursor.iternext_dup()]

    assert len(entries) == 2
    assert entries[0]["expire"] == expire
    assert entries[0]["offer"] == offer
    assert entries[1]["expire"] == expire1
    assert entries[1]["offer"] == offer

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_getOfferExpires():
    """
    Test get entries in did2offer database

    getOfferExpires(did, lastOnly=True, dbn='did2offer', env=None)
    """
    print("Testing getOfferExpires in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 1, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    #ouid = timing.tuuid(stamp=stamp, prefix="o")
    ouid = "o_00035d2976e6a000_26ace93"

    did = "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="
    expire = timing.iso8601(dt=dt, aware=True)
    assert expire == "2000-01-01T00:30:00+00:00"

    offer = "{}/offer/{}".format(did, ouid)
    assert offer == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=/offer/o_00035d2976e6a000_26ace93"

    #  no offer expire entries yet
    entries = dbing.getOfferExpires(did, lastOnly=False)
    assert entries == []

    # write entry
    result = dbing.putDidOfferExpire(did, ouid, expire)
    assert result == {
        'offer': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=/offer/o_00035d2976e6a000_26ace93',
        'expire': '2000-01-01T00:30:00+00:00'
        }

    # write another one
    td = datetime.timedelta(seconds=360)
    expire1 = timing.iso8601(dt=dt+td, aware=True)
    assert expire1 == "2000-01-01T00:36:00+00:00"

    result = dbing.putDidOfferExpire(did, ouid, expire1)
    assert result == {
        'offer': 'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=/offer/o_00035d2976e6a000_26ace93',
        'expire': '2000-01-01T00:36:00+00:00'
        }

    entries = dbing.getOfferExpires(did, lastOnly=False)
    assert len(entries) == 2
    assert entries[0]["expire"] == expire
    assert entries[0]["offer"] == offer
    assert entries[1]["expire"] == expire1
    assert entries[1]["offer"] == offer

    entries = dbing.getOfferExpires(did)  # lastOnly=True
    assert len(entries) == 1
    assert entries[0]["expire"] == expire1
    assert entries[0]["offer"] == offer

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_putGetDeleteAnon():
    """
    Test
    putAnonMsg(key, data, dbn="anon", env=None)
    getAnonMsgs(key, dbn='anon', env=None)
    deleteAnonMsgs(key, dbn='anon', env=None)

    where
        key is ephemeral ID 16 byte hex
        data is anon data

    The key for the entry is just the uid

    uid is up 32 bytes
        if anon ephemeral ID in base64 url safe
    content is message up to 256 bytes
         if location string in base 64 url safe
    date is iso8601 datetime

    This is augmented with server time stamp and stored in database
    {
        create: 1501774813367861, # creation in server time microseconds since epoch
        expire: 1501818013367861, # expiration in server time microseconds since epoch
        anon:
        {
            uid: "AQIDBAoLDA0=",  # base64 url safe of 8 byte eid
            content: "EjRWeBI0Vng=", # base64 url safe of 8 byte location
            date: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of anon gateway time
        }
    }
    """
    print("Testing put get delete Track in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 1, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    #create = timing.iso8601(dt=dt, aware=True)
    #assert create == '2000-01-01T00:30:00+00:00'
    create = int(dt.timestamp() * 1000000)
    assert create == 946686600000000

    #td = datetime.timedelta(seconds=360)
    #expire = timing.iso8601(dt=dt+td, aware=True)
    #assert expire == '2000-01-01T00:36:00+00:00'
    expire = create + (360 * 1000000)
    assert expire == 946686960000000

    # local time
    td = datetime.timedelta(seconds=5)
    date = timing.iso8601(dt=dt+td, aware=True)
    assert date == '2000-01-01T00:30:05+00:00'

    uid = "AQIDBAoLDA0="
    content = "EjRWeBI0Vng="

    anon = ODict()
    anon['uid'] = uid
    anon['content'] = content
    anon['date'] = date

    assert anon == {
        "uid": "AQIDBAoLDA0=",
        "content": "EjRWeBI0Vng=",
        "date": "2000-01-01T00:30:05+00:00",
    }

    data = ODict()
    data['create'] = create
    data['expire'] = expire
    data['anon'] = anon

    assert data == {
        "create": 946686600000000,
        "expire": 946686960000000,
        "anon":
        {
            "uid": "AQIDBAoLDA0=",
            "content": "EjRWeBI0Vng=",
            "date": "2000-01-01T00:30:05+00:00"
        }
    }

    # write entry
    result = dbing.putAnonMsg(key=uid, data=data)
    assert result

    # read entries
    entries = dbing.getAnonMsgs(key=uid)
    assert len(entries) == 1
    assert entries[0] == data

    anon2 = anon.copy()
    anon2['content'] = "ABRWeBI0VAA="
    data2 = ODict()
    data2['create'] = create + 1
    data2['expire'] = expire + 1
    data2['anon'] = anon2

    result = dbing.putAnonMsg(key=uid, data=data2)
    assert result

    # read entries
    entries = dbing.getAnonMsgs(key=uid)
    assert len(entries) == 2
    assert entries[0] == data
    assert entries[1] == data2

    uid2 = "BBIDBAoLCCC="
    anon3 = anon.copy()
    anon3["uid"] = uid2
    data3 = ODict()
    data3['create'] = create
    data3['expire'] = expire
    data3['anon'] = anon3

    result = dbing.putAnonMsg(key=uid2, data=data3)
    assert result

    # read entries
    entries = dbing.getAnonMsgs(key=uid2)
    assert len(entries) == 1
    assert entries[0] == data3

    # remove entries at uid
    result = dbing.deleteAnonMsgs(key=uid)
    assert result
    # read deleted entries
    entries = dbing.getAnonMsgs(key=uid)
    assert not entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

def test_getAllAnonUids():
    """
    Test
    getAllAnonUids(dbn="anon", env=None)

    Gets list of Anon Uids no dups

    The key for the entry is just the uid

    uid is up 32 bytes
        if anon ephemeral ID in base64 url safe

    """
    print("Testing put get delete Track in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 1, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    #create = timing.iso8601(dt=dt, aware=True)
    #assert create == '2000-01-01T00:30:00+00:00'
    create = int(dt.timestamp() * 1000000)
    assert create == 946686600000000

    #td = datetime.timedelta(seconds=360)
    #expire = timing.iso8601(dt=dt+td, aware=True)
    #assert expire == '2000-01-01T00:36:00+00:00'
    expire = create + (360 * 1000000)
    assert expire == 946686960000000

    # local time
    td = datetime.timedelta(seconds=5)
    date = timing.iso8601(dt=dt+td, aware=True)
    assert date == '2000-01-01T00:30:05+00:00'

    uid1 = "AQIDBAoLDA0="
    content = "EjRWeBI0Vng="

    anon1 = ODict()
    anon1['uid'] = uid1
    anon1['content'] = content
    anon1['date'] = date

    assert anon1 == {
        "uid": "AQIDBAoLDA0=",
        "content": "EjRWeBI0Vng=",
        "date": "2000-01-01T00:30:05+00:00",
    }

    data1 = ODict()
    data1['create'] = create
    data1['expire'] = expire
    data1['anon'] = anon1

    assert data1 == {
        "create": 946686600000000,
        "expire": 946686960000000,
        "anon":
        {
            "uid": "AQIDBAoLDA0=",
            "content": "EjRWeBI0Vng=",
            "date": "2000-01-01T00:30:05+00:00"
        }
    }

    # write entry
    result = dbing.putAnonMsg(key=uid1, data=data1)
    assert result
    anon2 = anon1.copy()
    anon2['content'] = "ABRWeBI0VAA="
    data2 = ODict()
    data2['create'] = create + 1
    data2['expire'] = expire + 1
    data2['anon'] = anon2

    result = dbing.putAnonMsg(key=uid1, data=data2)
    assert result

    uid2 = "BBIDBAoLCCC="
    anon3 = anon1.copy()
    anon3["uid"] = uid2
    data3 = ODict()
    data3['create'] = create
    data3['expire'] = expire
    data3['anon'] = anon3

    result = dbing.putAnonMsg(key=uid2, data=data3)
    assert result

    anon4 = anon1.copy()
    anon4["uid"] = uid2
    data4 = ODict()
    data4['create'] = create
    data4['expire'] = expire
    data4['anon'] = anon4

    result = dbing.putAnonMsg(key=uid2, data=data4)
    assert result

    entries = dbing.getAllAnonUids()
    assert len(entries) == 2
    assert uid1 in entries
    assert uid2 in entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")



def test_expireUid():
    """
    Test
    putExpireUid(expire, uid, dbn="expire2uid", env=None)
    getExpireUid(key, dbn='expire2uid', env=None)
    deleteExpireUid(key, dbn='expire2uid', env=None)

    where
        key is timestamp in int microseconds since epoch
        data is anon uid


    """
    print("Testing put get delete expire UID in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 3, minute=30, tzinfo=datetime.timezone.utc)
    expire = int(dt.timestamp() * 1000000)
    assert expire == 946859400000000

    td = datetime.timedelta(seconds=360)
    expire1 = expire + int(360 * 1000000)
    assert expire1 == 946859760000000

    uid = "00000000000="
    uid1 = "11111111111="
    uid2 = "22222222222="

    # write entry
    result = dbing.putExpireUid(key=expire, uid=uid)
    assert result

    # read entries
    entries = dbing.getExpireUid(key=expire)
    assert len(entries) == 1
    assert entries[0] == uid

    result = dbing.putExpireUid(key=expire, uid=uid1)
    assert result

    result = dbing.putExpireUid(key=expire, uid=uid2)
    assert result

    # read entries
    entries = dbing.getExpireUid(key=expire)
    assert len(entries) == 3
    assert entries[0] == uid
    assert entries[1] == uid1
    assert entries[2] == uid2

    # write entry
    result = dbing.putExpireUid(key=expire1, uid=uid)
    assert result

    entries = dbing.getExpireUid(key=expire1)
    assert len(entries) == 1
    assert entries[0] == uid

    # remove entries at expire
    result = dbing.deleteExpireUid(key=expire)
    assert result
    # read deleted entries
    entries = dbing.getExpireUid(key=expire)
    assert not entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_popExpired():
    """
    Test
    popExpired(key, dbn='expire2uid', env=None)

    where
        key is timestamp in int microseconds since epoch

    """
    print("Testing put get delete expire UID in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 3, minute=30, tzinfo=datetime.timezone.utc)
    expire0 = int(dt.timestamp() * 1000000)
    assert expire0 == 946859400000000

    expire1 = expire0 + int(360 * 1000000)
    assert expire1 == 946859760000000

    uid0 = "00000000000="
    uid1 = "11111111111="
    uid2 = "22222222222="
    uid3 = "33333333333="
    uid4 = "44444444444="
    uid5 = "55555555555="

    # write entries at expire
    result = dbing.putExpireUid(key=expire0, uid=uid0)
    assert result
    result = dbing.putExpireUid(key=expire0, uid=uid1)
    assert result
    result = dbing.putExpireUid(key=expire0, uid=uid2)
    assert result

    # read entries
    entries = dbing.getExpireUid(key=expire0)
    assert len(entries) == 3
    assert entries[0] == uid0
    assert entries[1] == uid1
    assert entries[2] == uid2


    # write entries
    result = dbing.putExpireUid(key=expire1, uid=uid3)
    assert result
    result = dbing.putExpireUid(key=expire1, uid=uid4)
    assert result
    result = dbing.putExpireUid(key=expire1, uid=uid5)
    assert result

    entries = dbing.getExpireUid(key=expire1)
    assert len(entries) == 3
    assert entries[0] == uid3
    assert entries[1] == uid4
    assert entries[2] == uid5

    # gets the earliest at expire0 before expire1
    entries = dbing.popExpired(key=expire1)
    assert len(entries) == 3
    assert entries[0] == uid0
    assert entries[1] == uid1
    assert entries[2] == uid2

    # attempt to read deleted entries at expire0
    entries = dbing.getExpireUid(key=expire0)
    assert not entries

    # gets the later at expire1 since expire0 has been deleted
    entries = dbing.popExpired(key=expire1)
    assert len(entries) == 3
    assert entries[0] == uid3
    assert entries[1] == uid4
    assert entries[2] == uid5

    # attempt to read deleted entries at expire1
    entries = dbing.getExpireUid(key=expire1)
    assert not entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_clearStaleAnons():
    """
    Test
    clearStaleAnonMsgs(key, adbn='anon', edbn='expire2uid', env=None)

    where
        key is timestamp in int microseconds since epoch

    """
    print("Testing Clear Stale Anon Msg in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 3, minute=30, tzinfo=datetime.timezone.utc)

    # local time
    td = datetime.timedelta(seconds=5)
    date = timing.iso8601(dt=dt+td, aware=True)
    assert date == '2000-01-03T00:30:05+00:00'
    content = "12341234123="

    create0 = int(dt.timestamp() * 1000000)
    expire0 = create0 + int(360 * 1000000)

    create1 = create0 + int(10 * 1000000)
    expire1 = create1 + int(360 * 1000000)

    uids0 = ["00000000000=", "10000000000=", "20000000000="]
    for uid in uids0:
        anon = ODict()
        anon['uid'] = uid
        anon['content'] = content
        anon['date'] = date

        data = ODict()
        data['create'] = create0
        data['expire'] = expire0
        data['track'] = anon

        # write entry
        result = dbing.putAnonMsg(key=uid, data=data)
        assert result
        result = dbing.putExpireUid(key=expire0, uid=uid)
        assert result

    # read entries
    for uid in uids0:
        entries = dbing.getAnonMsgs(key=uid)
        assert entries

    entries = dbing.getExpireUid(key=expire0)
    assert len(entries) == 3


    uids1 = ["30000000000=", "40000000000=", "50000000000="]
    for uid in uids1:
        anon = ODict()
        anon['uid'] = uid
        anon['content'] = content
        anon['date'] = date

        data = ODict()
        data['create'] = create1
        data['expire'] = expire1
        data['anon'] = anon

        # write entry
        result = dbing.putAnonMsg(key=uid, data=data)
        assert result
        result = dbing.putExpireUid(key=expire1, uid=uid)
        assert result

    # read entries
    for uid in uids1:
        entries = dbing.getAnonMsgs(key=uid)
        assert entries

    entries = dbing.getExpireUid(key=expire0)
    assert len(entries) == 3

    expire = expire0 - 1  # none expired
    result = dbing.clearStaleAnonMsgs(key=expire)
    assert not result

    expire = expire1  # all expired
    result = dbing.clearStaleAnonMsgs(key=expire)
    assert result

    # verify databases are empty
    uids = uids0 + uids1
    for uid in uids:
        entries = dbing.getAnonMsgs(key=uid)
        assert not entries

    expires = [expire0, expire1]
    for expire in expires:
        entries = dbing.getExpireUid(key=expire)
        assert not entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_preloadTestDbs():
    """
    Test preloadTestDbs

    """
    print("Testing staging dbs")
    priming.setupTest()
    dbEnv = dbing.gDbEnv
    dbing.preloadTestDbs()

    agents = dbing.getAgents()
    assert agents == ['did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=',
                    'did:igo:QBRKvLW1CnVDIgznfet3rpad-wZBL4qGASVpGRsE2uU=',
                    'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=',
                    'did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=',
                    'did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=']


    things = dbing.getThings()
    assert things == ['did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=']

    did = dbing.getHid(key="hid:dns:localhost#02")
    assert did == things[0]

    #test get inbox for Ivy
    messages = dbing.getDrops("did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=")
    assert len(messages) == 2
    assert messages[0]['from'] == "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE="

    #test get inbox for Ann
    messages = dbing.getDrops("did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=")
    assert len(messages) == 1
    assert messages[0]['from'] == "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="

    entries = dbing.getOfferExpires('did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=',
                                    lastOnly=False)
    assert len(entries) == 2

    dat, ser, sig = dbing.getSigned(entries[0]["offer"])
    assert dat["uid"] == 'o_00035d2976e6a000_26ace93'

    auids = dbing.getAllAnonUids()
    assert auids == ['AQIDBAoLDA0=', 'BBIDBAoLCCC=']

    anons = dbing.getAnonMsgs(key=auids[0])
    assert len(anons) == 3

    anons = dbing.getAnonMsgs(key=auids[1])
    assert len(anons) == 1

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")

