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
                                  parseSignatureHeader, verify, makeDid,
                                  key64uToKey, keyToKey64u,
                                  makeSignedAgentReg, validateSignedAgentReg,
                                  makeSignedThingReg, validateSignedThingReg,
                                  validateSignedResource, )


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
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    vk, sk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    issuant = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    issuants = [issuant]  # list of hid issuants

    signature, registration = makeSignedAgentReg(vk,
                                                 sk,
                                                 changed=stamp,
                                                 issuants=issuants)

    assert len(signature) == 88
    assert signature == ('Fgn0uNoZ4OqJrqiKv03HotWztrrM2ZPapf-977nZEtlpk6JPywuFFem6f4UZOZkNcvAbfUalwAr29nkX5P6ADg==')

    assert len(registration) == 477
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

    # validate
    reg = validateSignedAgentReg(signature, registration)

    assert reg is not None

    assert vk == key64uToKey(reg["keys"][0]["key"])

    print("Done Test")


def test_signedThingRegistrationWithData():
    """
    Test helper function
    """
    print("Testing makeSignedThingRegistration")

    # random seed used to generate private signing key
    #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
    seed = (b'PTi\x15\xd5\xd3`\xf1u\x15}^r\x9bfH\x02l\xc6\x1b\x1d\x1c\x0b9\xd7{\xc0_'
            b'\xf2K\x93`')

    # creates signing/verification key pair
    svk, ssk = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    sdid = makeDid(svk)  # create the did
    index = 0
    signer = "{}#{}".format(sdid, index)  # signer field value key at index

    seed = (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
            b'P\xdd&R <\x97\x01')


    dvk, dsk = libnacl.crypto_sign_seed_keypair(seed)
    assert dvk == (b'\xe0\x90\x8c\xf1\xd2V\xc3\xf3\xb9\xee\xf38\x90\x0bS\xb7L\x96\xa9('
                   b'\x01\xbb\x08\x87\xa5X\x1d\xe7\x90b\xa0#')
    assert dsk == (b'\xba^\xe4\xdd\x81\xeb\x8b\xfa\xb1k\xe2\xfd6~^\x86tC\x9c\xa7\xe3\x1d2\x9d'
                   b'P\xdd&R <\x97\x01\xe0\x90\x8c\xf1\xd2V\xc3\xf3\xb9\xee\xf38\x90\x0bS\xb7'
                    b'L\x96\xa9(\x01\xbb\x08\x87\xa5X\x1d\xe7\x90b\xa0#')


    hid = "hid:dns:generic.com#02"
    data = ODict(keywords=["Canon", "EOS Rebel T6", "251440"],
                 message="If found please return.")

    dsignature, ssignature, tregistration = makeSignedThingReg(dvk,
                                                               dsk,
                                                               ssk,
                                                               signer=signer,
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

    # validate
    reg = validateSignedThingReg(dsignature, tregistration)
    assert reg is not None

    sverkey = keyToKey64u(svk)
    rsrc = validateSignedResource(ssignature, resource=tregistration, verkey=sverkey)
    assert rsrc

    print("Done Test")
