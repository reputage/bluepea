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

import libnacl
import libnacl.sign

import pytest
from pytest import approx

from bluepea.help.helping import (setupTmpBaseDir, cleanupBaseDir, dumpKeys, loadKeys,
                                  verify, makeDid, key64uToKey, keyToKey64u)





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

    keyDataFiled = loadKeys(keyFilePath)
    assert keyData == keyDataFiled

    sd = binascii.unhexlify(keyDataFiled['seed'].encode('utf-8'))
    assert sd == seed
    sk = binascii.unhexlify(keyDataFiled['sigkey'].encode('utf-8'))
    assert sk == sigkey
    vk = binascii.unhexlify(keyDataFiled['verkey'].encode('utf-8'))
    assert vk == verkey

    cleanupBaseDir(baseDirPath)
    print("Done Test")

def test_makeDid():
    """

    """
    print("Testing makeDid keys")


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
    assert "\r\n\r\n" not in regser  # separator
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