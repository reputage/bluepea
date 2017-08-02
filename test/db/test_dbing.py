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
                                  makeSignedAgentReg, makeSignedThingReg)

from bluepea.db import dbing


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
        cursor = txn.cursor()
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

def test_putGetDeleteTrack():
    """
    Test
    putTrack(key, data, dbn="track", env=None)
    getTracks(key, dbn='track', env=None)
    deleteTracks(key, dbn='track', env=None)

    where
        key is ephemeral ID 16 byte hex
        data is track data

    The key for the entry is just the eid

    The value of the entry is serialized JSON
    {
        create: "2000-01-01T00:36:00+00:00", # ISO-8601 creation in server time
        expire: "2000-01-01T12:36:00+00:00", # ISO-8601 expiration in server time
        track:
        {
            eid: "abcdef0123456789,  # lower case 16 char hex of 8 byte eid
            loc: "1111222233334444", # lower case 16 char hex of 8 byte location
            dts: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of track gateway time
        }
    }
    """
    print("Testing put get delete Track in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 1, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    create = timing.iso8601(dt=dt, aware=True)
    assert create == '2000-01-01T00:30:00+00:00'

    td = datetime.timedelta(seconds=360)
    expire = timing.iso8601(dt=dt+td, aware=True)
    assert expire == '2000-01-01T00:36:00+00:00'

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

    data = ODict()
    data['create'] = create
    data['expire'] = expire
    data['track'] = track

    assert data == {
        "create": "2000-01-01T00:30:00+00:00",
        "expire": "2000-01-01T00:36:00+00:00",
        "track":
        {
            "eid": "010203040a0b0c0d",
            "loc": "1234567812345678",
            "dts": "2000-01-01T00:30:05+00:00"
        }
    }

    # write entry
    result = dbing.putTrack(key=eid, data=data)
    assert result

    # read entries
    entries = dbing.getTracks(key=eid)
    assert len(entries) == 1
    assert entries[0] == data

    track2 = track.copy()
    track2['loc'] = "98765432987865432"
    data2 = ODict()
    data2['create'] = create
    data2['expire'] = expire
    data2['track'] = track2

    result = dbing.putTrack(key=eid, data=data2)
    assert result

    # read entries
    entries = dbing.getTracks(key=eid)
    assert len(entries) == 2
    assert entries[0] == data
    assert entries[1] == data2

    eid2 = "1212121234343434"
    track3 = track.copy()
    track3["eid"] = eid2
    data3 = ODict()
    data2['create'] = create
    data2['expire'] = expire
    data2['track'] = track3

    result = dbing.putTrack(key=eid2, data=data3)
    assert result

    # read entries
    entries = dbing.getTracks(key=eid2)
    assert len(entries) == 1
    assert entries[0] == data3

    # remove entries at eid
    result = dbing.deleteTracks(key=eid)
    assert result
    # read deleted entries
    entries = dbing.getTracks(key=eid)
    assert not entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")


def test_expireEid():
    """
    Test
    putExpireEid(expire, eid, dbn="expire2eid", env=None)
    getExpireEid(key, dbn='expire2eid', env=None)
    deleteExpireEid(key, dbn='expire2eid', env=None)

    where
        key is is8601 datetime
        data is track eid


    """
    print("Testing put get delete expire Eid in DB Env")

    dbEnv = dbing.setupTestDbEnv()

    dt = datetime.datetime(2000, 1, 3, minute=30, tzinfo=datetime.timezone.utc)
    #stamp = dt.timestamp()  # make time.time value
    expire = timing.iso8601(dt=dt, aware=True)
    assert expire == '2000-01-03T00:30:00+00:00'

    td = datetime.timedelta(seconds=360)
    expire1 = timing.iso8601(dt=dt+td, aware=True)
    assert expire1 == '2000-01-03T00:36:00+00:00'

    eid = "010203040a0b0c0d"
    eid1 = "1212121234343434"
    eid2 = "2200000034343434"

    # write entry
    result = dbing.putExpireEid(key=expire, eid=eid)
    assert result

    # read entries
    entries = dbing.getExpireEid(key=expire)
    assert len(entries) == 1
    assert entries[0] == eid

    result = dbing.putExpireEid(key=expire, eid=eid1)
    assert result

    result = dbing.putExpireEid(key=expire, eid=eid2)
    assert result

    # read entries
    entries = dbing.getExpireEid(key=expire)
    assert len(entries) == 3
    assert entries[0] == eid
    assert entries[1] == eid1
    assert entries[2] == eid2

    # write entry
    result = dbing.putExpireEid(key=expire1, eid=eid)
    assert result

    entries = dbing.getExpireEid(key=expire1)
    assert len(entries) == 1
    assert entries[0] == eid

    # remove entries at expire
    result = dbing.deleteExpireEid(key=expire)
    assert result
    # read deleted entries
    entries = dbing.getExpireEid(key=expire)
    assert not entries

    cleanupTmpBaseDir(dbEnv.path())
    print("Done Test")
