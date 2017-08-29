from __future__ import generator_stop

import os
import stat
import tempfile
import shutil
import binascii
import base64
import datetime
import copy

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
                                  parseSignatureHeader, verify, makeDid,
                                  key64uToKey, keyToKey64u,
                                  makeSignedAgentReg, validateSignedAgentReg,
                                  makeSignedThingReg, validateSignedThingReg,
                                  validateSignedResource, validateSignedAgentWrite)


def test_parseSignatureHeader():
    """
    Test helper function to parse signature header
    """
    print("Testing parseSignatureHeader")

    signature = None
    sigs = parseSignatureHeader(signature)
    assert len(sigs) == 0

    signature = ('did="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz'
                 'QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="')
    sigs = parseSignatureHeader(signature)
    assert sigs['did'] == ("B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz"
                           "QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==")

    signature = ('did = "B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz'
                 'QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="  ;  ')
    sigs = parseSignatureHeader(signature)
    assert sigs['did'] == ("B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz"
                           "QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==")

    signature = ('did="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz'
                 'QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==";'
                 'signer="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz'
                 'QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==";'
                 'kind="EdDSA";')
    sigs = parseSignatureHeader(signature)
    assert sigs['did'] == ("B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz"
                           "QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==")
    assert sigs['did'] == ("B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz"
                           "QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==")
    assert sigs['kind'] == "EdDSA"

    print("Done Test")


def test_makeDidSign():
    """
    Testing utility functions for did keys and signature
    """
    print("Testing makeDid and Signature keys")

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    # create registration record as dict
    reg = ODict()

    did = makeDid(vk)  # create the did
    assert did.startswith("did:igo:")
    assert len(did) == 52

    signer = "{}#0".format(did)  # make signer field value to be key index 0

    didy, index = signer.rsplit("#", maxsplit=1)
    index = int(index)
    assert index ==  0

    verkey = keyToKey64u(vk)  # make key index field value
    kind = "EdDSA"

    reg["did"] = did
    reg["signer"] = signer
    reg["keys"] = [ODict(key=verkey, kind=kind)]

    assert reg["keys"][index]["key"] == verkey

    assert reg == ODict([
        ('did', 'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='),
        ('signer',
            'did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0'),
        ('keys',
            [
                ODict([
                    ('key', 'Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE='),
                    ('kind', 'EdDSA')
                ])
            ])
    ])

    regser = json.dumps(reg, indent=2)
    assert len(regser) == 249
    assert SEPARATOR not in regser  # separator
    assert regser == ('{\n'
                      '  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
                      '  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",\n'
                      '  "keys": [\n'
                      '    {\n'
                      '      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",\n'
                      '      "kind": "EdDSA"\n'
                      '    }\n'
                      '  ]\n'
                      '}')

    regdeser = json.loads(regser, object_pairs_hook=ODict)
    assert reg == regdeser
    regserb = regser.encode("utf-8")  # re convert to bytes
    rregser = regserb.decode("utf-8")  # reconvert
    assert rregser == regser  # roundtrip

    # sign bytes
    sig = libnacl.crypto_sign(regserb, sk)[:libnacl.crypto_sign_BYTES]
    assert len(sig) == 64
    signature = keyToKey64u(sig)
    assert len(signature) == 88
    assert signature == ('B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz'
                         'QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==')

    rsig = key64uToKey(signature)
    assert rsig == sig

    result = verify(sig, regserb, vk)
    assert result

    print("Done Test")


def test_signedAgentRegistration():
    """
    Test helper function
    """
    print("Testing makeSignedAgentRegistration")

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    signature, registration = makeSignedAgentReg(vk, sk, changed=stamp)

    assert len(signature) == 88
    assert signature == ('AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKBYrPP'
                         'xAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg==')

    assert len(registration) == 291
    assert SEPARATOR not in registration  # separator
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

    # validate
    reg = validateSignedAgentReg(signature, registration)

    assert reg is not None

    assert vk == key64uToKey(reg["keys"][0]["key"])

    print("Done Test")


def test_signedAgentRegistrationWithData():
    """
    Test helper function
    """
    print("Testing makeSignedAgentRegistration")

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    # Ann's seed
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    date = timing.iso8601(dt, aware=True)
    assert  date == "2000-01-01T00:00:00+00:00"

    issuant = ODict(kind="dns",
                issuer="localhost",
                registered=date,
                validationURL="http://localhost:8080/demo/check")
    issuants = [issuant]  # list of hid issuants

    sig, ser = makeSignedAgentReg(vk, sk, changed=date, issuants=issuants)

    assert len(sig) == 88
    assert sig == 'ELqC0M2G8Fs4Z1FCPP0E2jrfJFbAYKoAu-tDn0G05w7ecb4pqN_8pQuruZs-KbCEzTOHov1OWkZ_fSuFZZKzDA=='

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
        '  ],\n'
        '  "issuants": [\n'
        '    {\n'
        '      "kind": "dns",\n'
        '      "issuer": "localhost",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "http://localhost:8080/demo/check"\n'
        '    }\n'
        '  ]\n'
        '}')

    # validate
    dat = validateSignedAgentReg(sig, ser)
    assert dat is not None
    assert vk == key64uToKey(dat["keys"][0]["key"])

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    # Ivy's seed
    seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
            b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    date = timing.iso8601(dt, aware=True)
    assert  date == "2000-01-01T00:00:00+00:00"

    issuant = ODict(kind="dns",
                    issuer="localhost",
                registered=date,
                validationURL="http://localhost:8080/demo/check")
    issuants = [issuant]  # list of hid issuants

    sig, ser = makeSignedAgentReg(vk, sk, changed=date, issuants=issuants)

    assert len(sig) == 88
    assert sig == 'jc3ZXMA5GuypGWFEsxrGVOBmKDtd0J34UKZyTIYUMohoMYirR8AgH5O28PSHyUB-UlwfWaJlibIPUmZVPTG1DA=='

    assert SEPARATOR not in ser  # separator
    assert ser == (
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
        '      "issuer": "localhost",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "http://localhost:8080/demo/check"\n'
        '    }\n'
        '  ]\n'
        '}')

    # validate
    dat = validateSignedAgentReg(sig, ser)
    assert dat is not None
    assert vk == key64uToKey(dat["keys"][0]["key"])

    # add new key
    ndat = copy.copy(dat)
    seed = (b'Z\xda?\x93M\xf8|\xe2!d\x16{s\x9d\x07\xd2\x98\xf2!\xff\xb8\xb6\xf9Z'
            b'\xe5I\xbc\x97}IFV')
    # creates signing/verification key pair
    nvk, nsk = libnacl.crypto_sign_seed_keypair(seed)

    ndt = datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc)
    ndate = timing.iso8601(ndt, aware=True)
    ndat['changed'] = ndate
    index = 1
    signer = "{}#{}".format(dat['did'], index)  # signer field value key at index
    ndat['signer'] = signer
    nverkey = keyToKey64u(nvk)  # make key index field value
    assert nverkey == '0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI='
    kind = "EdDSA"
    ndat['keys'].append(ODict(key=nverkey, kind="EdDSA"))

    ser = json.dumps(ndat, indent=2)
    assert ser == (
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
        '      "issuer": "localhost",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "http://localhost:8080/demo/check"\n'
        '    }\n'
        '  ]\n'
        '}')

    # sign new record with old key
    sig = keyToKey64u(libnacl.crypto_sign(ser.encode("utf-8"), sk)[:libnacl.crypto_sign_BYTES])
    assert sig == 'bTGB92MvNmb65Ka0BD7thquxw1BGEcJRf1c8GpTvcF5Qe-tm0v28qMGKfYQ3EYeVI1VdLWRMtyFApnyAB07yCQ=='
    assert vk == key64uToKey(dat["keys"][0]["key"])

    # sign new record with new key
    nsig = keyToKey64u(libnacl.crypto_sign(ser.encode("utf-8"), nsk)[:libnacl.crypto_sign_BYTES])
    assert nsig == 'o9yjuKHHNJZFi0QD9K6Vpt6fP0XgXlj8z_4D-7s3CcYmuoWAh6NVtYaf_GWw_2sCrHBAA2mAEsml3thLmu50Dw=='
    ndat = validateSignedAgentWrite(dat, sig, nsig, ser)
    assert ndat is not None
    assert nvk == key64uToKey(ndat["keys"][1]["key"])


    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    # Ike's seed
    seed = (b'!\x85\xaa\x8bq\xc3\xf8n\x93]\x8c\xb18w\xb9\xd8\xd7\xc3\xcf\x8a\x1dP\xa9m'
            b'\x89\xb6h\xfe\x10\x80\xa6S')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    date = timing.iso8601(dt, aware=True)
    assert  date == "2000-01-01T00:00:00+00:00"

    issuant = ODict(kind="dns",
                    issuer="localhost",
                    registered=date,
                validationURL="http://localhost:8080/demo/check")
    issuants = [issuant]  # list of hid issuants

    sig, ser = makeSignedAgentReg(vk, sk, changed=date, issuants=issuants)

    assert len(sig) == 88
    assert sig == '1HO_9ERLOe30yEQyiwgu7g9DeHC8Nsq-ybQlNtDW9D611J61gm52Na5Cx5acYu71X8g_UR4Eyj05saNBoqcnCw=='

    assert SEPARATOR not in ser  # separator
    assert ser == (
        '{\n'
        '  "did": "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=",\n'
        '  "signer": "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=#0",\n'
        '  "changed": "2000-01-01T00:00:00+00:00",\n'
        '  "keys": [\n'
        '    {\n'
        '      "key": "3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=",\n'
        '      "kind": "EdDSA"\n'
        '    }\n'
        '  ],\n'
        '  "issuants": [\n'
        '    {\n'
        '      "kind": "dns",\n'
        '      "issuer": "localhost",\n'
        '      "registered": "2000-01-01T00:00:00+00:00",\n'
        '      "validationURL": "http://localhost:8080/demo/check"\n'
        '    }\n'
        '  ]\n'
        '}')

    # validate
    dat = validateSignedAgentReg(sig, ser)
    assert dat is not None
    assert vk == key64uToKey(dat["keys"][0]["key"])

    print("Done Test")


def test_signedThingRegistrationWithData():
    """
    Test helper function
    """
    print("Testing makeSignedThingRegistration")

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    # Ivy's seed
    seed = (b"\xb2PK\xad\x9b\x92\xa4\x07\xc6\xfa\x0f\x13\xd7\xe4\x08\xaf\xc7'~\x86"
            b'\xd2\x92\x93rA|&9\x16Bdi')

    # creates signing/verification key pair
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    date = timing.iso8601(dt, aware=True)
    assert  date == "2000-01-01T00:00:00+00:00"

    sdid = makeDid(svk)  # create the did
    index = 0
    signer = "{}#{}".format(sdid, index)  # signer field value key at index

    # cam's seed
    seed = (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
            b'P\xdd&R <\x97\x01')


    dvk, dsk = libnacl.crypto_sign_seed_keypair(seed)
    assert dvk == (b'\xe0\x90\x8c\xf1\xd2V\xc3\xf3\xb9\xee\xf38\x90\x0bS\xb7L\x96\xa9('
                   b'\x01\xbb\x08\x87\xa5X\x1d\xe7\x90b\xa0#')
    assert dsk == (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
                   b'P\xdd&R <\x97\x01\xe0\x90\x8c\xf1\xd2V\xc3\xf3\xb9\xee\xf38\x90\x0bS\xb7'
                    b'L\x96\xa9(\x01\xbb\x08\x87\xa5X\x1d\xe7\x90b\xa0#')


    hid = "hid:dns:localhost#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    dsig, ssig, ser = makeSignedThingReg(dvk,
                                                               dsk,
                                                               ssk,
                                                               signer=signer,
                                                               changed=date,
                                                               hid=hid,
                                                               data=data)


    assert ser == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:localhost#02",\n'
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

    assert dsig == 'bzJDEvEprraZc9aOLYS7WaPi5UB_px0EH9wu76rFPrbRgjAUO9JJ4roMpQrD31v3WlbHHTG8WzB5L8PE6v3BCg=='

    assert ssig == 'FGRHzSNS70LIjwcSTAxHx5RahDwAet090fYSnsReMco_WvpTVpvfEygWDXslCBh0TqBoEOMLQ78-kN8fj6NFAg=='

    # validate
    dat = validateSignedThingReg(dsig, ser)
    assert dat is not None
    sverkey = keyToKey64u(svk)
    rsrc = validateSignedResource(ssig, resource=ser, verkey=sverkey)
    assert rsrc

    # make copy
    ndat = copy.copy(dat)

    # change signer
    # make new key  another key for someone
    seed = (b'Z\xda?\x93M\xf8|\xe2!d\x16{s\x9d\x07\xd2\x98\xf2!\xff\xb8\xb6\xf9Z'
            b'\xe5I\xbc\x97}IFV')
    # creates signing/verification key pair
    nvk, nsk = libnacl.crypto_sign_seed_keypair(seed)

    signer = "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1"
    ndat['signer'] = signer
    ndt = datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc)
    ndate = timing.iso8601(ndt, aware=True)
    ndat['changed'] = ndate
    ser = json.dumps(ndat, indent=2)
    assert ser == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
        '  "hid": "hid:dns:localhost#02",\n'
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

    # sign new record with old key
    sig = keyToKey64u(libnacl.crypto_sign(ser.encode("utf-8"), ssk)[:libnacl.crypto_sign_BYTES])
    assert sig == 'fuSvUsNtFDzaYm5bX65SAgrZpNKEek2EJFqf-j-_QRWNXhSWpTFGIeg4AHOVaD7MHuIj6QsnjPg-jyBDiUAmCw=='

    # sign new record with new key
    nsig = keyToKey64u(libnacl.crypto_sign(ser.encode("utf-8"), nsk)[:libnacl.crypto_sign_BYTES])
    assert nsig == '4IMop_e8vDbsot2kqJaZin8_xPsayWKbpsXL2qJZc3NrB6254UNi9x5VRwk-OgYn0zQPvKwtTE8GjtYZAHaKAQ=='
    sverkey = keyToKey64u(nvk)
    rsrc = validateSignedResource(nsig, resource=ser, verkey=sverkey)
    assert rsrc

    # make copy
    ndat = copy.copy(dat)

    # change signer to ann
    # make new key with Ann's seed
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')
    # creates signing/verification key pair
    nvk, nsk = libnacl.crypto_sign_seed_keypair(seed)
    signer = "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0"
    ndat['signer'] = signer
    # remove hid
    del ndat['hid']
    ser = json.dumps(ndat, indent=2)
    assert ser == (
        '{\n'
        '  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",\n'
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

    # sign new record with new key
    nsig = keyToKey64u(libnacl.crypto_sign(ser.encode("utf-8"), nsk)[:libnacl.crypto_sign_BYTES])
    assert nsig == 'c04xu10KP_O8gfWoVvHRw8sO7ww9WrQ91BT_HXNGtSEMTf_BsKikxSUyQz0ASxjscEJVvV6E7yaldQ0dECQgAQ=='
    sverkey = keyToKey64u(nvk)
    rsrc = validateSignedResource(nsig, resource=ser, verkey=sverkey)
    assert rsrc


    print("Done Test")
