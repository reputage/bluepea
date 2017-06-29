# -*- encoding: utf-8 -*-
"""
Helping Module

"""
from __future__ import generator_stop

import os
import stat
from collections import OrderedDict as ODict, deque
import enum
import binascii
import base64

try:
    import simplejson as json
except ImportError:
    import json

try:
    import msgpack
except ImportError:
    pass

from ioflo.aid.sixing import *
from ioflo.aid import getConsole
from ioflo.aid import filing

import libnacl
import libnacl.sign

console = getConsole()

def setupTmpBaseDir(baseDirPath=""):
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


def dumpKeys(data, filepath):
    '''
    Write data as as type self.ext to filepath. json or msgpack
    '''
    if ' ' in filepath:
        raise IOError("Invalid filepath '{0}' "
                                "contains space".format(filepath))

    perm_other = stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
    perm_group = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
    cumask = os.umask(perm_other | perm_group)  # save old into cumask and set new

    root, ext = os.path.splitext(filepath)
    if ext == '.json':
        with filing.ocfn(filepath, "w+") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.msgpack':
        if not msgpack:
            raise IOError("Invalid filepath ext '{0}' "
                        "needs msgpack installed".format(filepath))
        with filing.ocfn(filepath, "w+b", binary=True) as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError("Invalid filepath ext '{0}' "
                    "not '.json' or '.msgpack'".format(filepath))

    os.umask(cumask)  # restore old


def loadKeys(filepath):
    '''
    Return data read from filepath as converted json
    Otherwise return None
    '''
    try:
        root, ext = os.path.splitext(filepath)
        if ext == '.json':
            with filing.ocfn(filepath, "r") as f:
                it = json.load(f, object_pairs_hook=ODict)
        elif ext == '.msgpack':
            if not msgpack:
                raise IOError("Invalid filepath ext '{0}' "
                            "needs msgpack installed".format(filepath))
            with filing.ocfn(filepath, "rb", binary=True) as f:
                it = msgpack.load(f, object_pairs_hook=ODict)
        else:
            it = None
    except EOFError:
        return None
    except ValueError:
        return None
    return it



def keyToKey64u(key):
    """
    Convert and return bytes key to unicode base64 url-file safe version
    """
    return base64.urlsafe_b64encode(key).decode("utf-8")

def key64uToKey(key64u):
    """
    Convert and return unicode base64 url-file safe key64u to bytes key
    """
    return base64.urlsafe_b64decode(key64u.encode("utf-8"))

def makeDid(verkey, method="igo"):
    """
    Create and return Indigo Did from bytes verkey.
    verkey is 32 byte verifier key from EdDSA (Ed25519) keypair
    """
    # convert verkey to jsonable unicode string of base64 url-file safe
    vk64u = base64.urlsafe_b64encode(verkey).decode("utf-8")
    did = "did:{}:{}".format(method, vk64u)
    return did

def verify(sig, msg, vk):
    """
    Returns message if signature sig of message msg is verified with
    verification key vk
    All of sig, msg, vk are bytes
    """
    return (libnacl.crypto_sign_open(sig + msg, vk))

def verify64u(signature, message, verkey):
    """
    Returns True if signature is valid for message with respect to verification
    key verkey

    signature and verkey are encoded as unicode base64 url-file strings
    and message is unicode string as would be the case for a json object

    """
    sig = key64uToKey(signature)
    vk = key64uToKey(verkey)
    msg = message.encode("utf-8")

    return True if verify(sig, msg, vk) else False


def makeAgentRegistration(vk, sk):
    """
    Return duple of (registration, signature) of minimal self-signing
    agent registration record for keypair vk, sk


    vk and sk are bytes
    vk is the public verification key and sk is the private signing key

    registration is json encoded unicode string of registration record
    signature is base64 url-file safe unicode string signature generated
    by signing bytes version of registration
    """
    reg = ODict()  # create registration record as dict

    did = makeDid(verkey)  # create the did
    index = 0
    signer = "{}#{}".format(did, index)  # signer field value key at index
    key64u = keyToKey64u(verkey)  # make key index field value
    kind = "EdDSA"

    reg["did"] = did
    reg["signer"] = signer
    reg["keys"] = [ODict(key=key64u, kind=kind)]

    msg = json.dumps(reg, indent=2).encode("utf-8")
    sig = libnacl.crypto_sign(msg, sk)[:libnacl.crypto_sign_BYTES]
    signature = keyToKey64u(sig)

    reutrn (registration, signature)
