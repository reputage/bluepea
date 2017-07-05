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
import libnacl.sign

from ioflo.aid import timing

import pytest
from pytest import approx

from bluepea.help.helping import (SEPARATOR, setupTmpBaseDir, cleanupTmpBaseDir,
                                  dumpKeys, loadKeys,
                                  parseSignatureHeader, verify, makeDid,
                                  key64uToKey, keyToKey64u,
                                  makeSignedAgentReg, validateSignedAgentReg)


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

    dumpKeys(keyData, keyFilePath)
    assert os.path.exists(keyFilePath)
    mode = stat.filemode(os.stat(keyFilePath).st_mode)
    assert mode == "-rw-------"

    keyDataFiled = loadKeys(keyFilePath)
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
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    # create registration record as dict
    reg = ODict()

    did = makeDid(verkey)  # create the did
    assert did.startswith("did:igo:")
    assert len(did) == 52

    signer = "{}#0".format(did)  # make signer field value to be key index 0

    didy, index = signer.rsplit("#", maxsplit=1)
    index = int(index)
    assert index ==  0

    key64u = keyToKey64u(verkey)  # make key index field value
    kind = "EdDSA"

    reg["did"] = did
    reg["signer"] = signer
    reg["keys"] = [ODict(key=key64u, kind=kind)]

    assert reg["keys"][index]["key"] == key64u

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
    sig = libnacl.crypto_sign(regserb, sigkey)[:libnacl.crypto_sign_BYTES]
    assert len(sig) == 64
    signature = keyToKey64u(sig)
    assert len(signature) == 88
    assert signature == ('B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmz'
                         'QFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==')

    rsig = key64uToKey(signature)
    assert rsig == sig

    result = verify(sig, regserb, verkey)
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
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    signature, registration = makeSignedAgentReg(verkey, sigkey, changed=stamp)

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

    assert verkey == key64uToKey(reg["keys"][0]["key"])

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
    verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)

    dt = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    stamp = timing.iso8601(dt, aware=True)
    assert  stamp == "2000-01-01T00:00:00+00:00"

    hid = ODict(kind="dns",
                issuer="generic.com",
                registered=stamp,
                validationURL="https://generic.com/indigo")
    hids = [hid]  # list of hids

    signature, registration = makeSignedAgentReg(verkey,
                                                 sigkey,
                                                 changed=stamp,
                                                 hids=hids)

    assert len(signature) == 88
    assert signature == ('f2w1L6XtU8_GS5N8UwX0d77aw2kR0IM5BVdBLOaoIyR9nzra6d4J'
                         'gVV7TlJrEx8WhJlgBRpyInRZgdnSf_WQAg==')

    assert len(registration) == 473
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
        '  "hids": [\n'
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

    assert verkey == key64uToKey(reg["keys"][0]["key"])

    print("Done Test")
