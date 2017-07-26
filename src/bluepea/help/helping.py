# -*- encoding: utf-8 -*-
"""
Helping Module

"""
from __future__ import generator_stop

import os
import stat
import shutil
from collections import OrderedDict as ODict, deque
import enum
import binascii
import base64
import tempfile
import datetime

try:
    import simplejson as json
except ImportError:
    import json

try:
    import msgpack
except ImportError:
    pass

import arrow

from ioflo.aid.sixing import *
from ioflo.aid import getConsole
from ioflo.aid import filing
from ioflo.aid import timing

import libnacl

from ..bluepeaing import SEPARATOR, PROPAGATION_DELAY

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

def cleanupTmpBaseDir(baseDirPath):
    """
    Remove temporary root of baseDirPath
    Ascend tree to find temporary root directory
    """
    if os.path.exists(baseDirPath):
        while baseDirPath.startswith("/tmp/bluepea"):
            if baseDirPath.endswith("test"):
                shutil.rmtree(baseDirPath)
                break
            baseDirPath = os.path.dirname(baseDirPath)

def cleanupBaseDir(baseDirPath):
    """
    Remove baseDirPath
    """
    if os.path.exists(baseDirPath):
        shutil.rmtree(baseDirPath)


def parseSignatureHeader(signature):
    """
    Returns ODict of fields and values parsed from signature
    which is the value portion of a Signature header

    Signature header has format:

        Signature: headervalue

    Headervalue:
        tag = "signature"

    or

        tag = "signature"; tag = "signature"  ...

    where tag is the name of a field in the body of the request whose value
    is a DID from which the public key for the signature can be obtained
    If the same tag appears multiple times then only the last occurrence is returned

    each signature value is a doubly quoted string that contains the actual signature
    in Base64 url safe format. By default the signatures are EdDSA (Ed25519)
    which are 88 characters long (with two trailing pad bytes) that represent
    64 byte EdDSA signatures

    An option tag name = "kind" with values "EdDSA"  "Ed25519" may be present
    that specifies the type of signature. All signatures within the header
    must be of the same kind.

    The two tag fields currently supported are "did" and "signer"


    """
    sigs = ODict()
    if signature:
        clauses = signature.split(";")
        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue
            try:
                tag, value = clause.split("=", maxsplit=1)
            except ValueError as ex:
                continue
            tag = tag.strip()
            if not tag:
                continue
            value = value.strip()
            if not value.startswith('"') or not value.endswith('"') or len(value) < 3:
                continue
            value = value[1:-1]
            value = value.strip()
            sigs[tag] = value

    return sigs

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

def makeDid(vk, method="igo"):
    """
    Create and return Indigo Did from bytes vk.
    vk is 32 byte verifier key from EdDSA (Ed25519) keypair
    """
    # convert verkey to jsonable unicode string of base64 url-file safe
    vk64u = base64.urlsafe_b64encode(vk).decode("utf-8")
    did = "did:{}:{}".format(method, vk64u)
    return did

def verify(sig, msg, vk):
    """
    Returns True if signature sig of message msg is verified with
    verification key vk Otherwise False
    All of sig, msg, vk are bytes
    """
    try:
        result = libnacl.crypto_sign_open(sig + msg, vk)
    except Exception as ex:
        return False
    return (True if result else False)

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
    return (verify(sig, msg, vk))

def extractDatSignerParts(dat, method="igo"):
    """
    Parses and returns did index keystr from signer field value of dat
    as tuple (did, index, keystr)
    raises ValueError if fails parsing
    """
    # get signer key from read data. assumes that resource is valid
    try:
        did, index = dat["signer"].rsplit("#", maxsplit=1)
        index = int(index)  # get index and sdid from signer field
    except (KeyError, ValueError) as ex:
        raise ValueError("Missing signer field or invalid indexed signer value")

    try:  # correct did format  pre:method:keystr
        pre, meth, keystr = did.split(":")
    except ValueError as ex:
        raise ValueError("Malformed DID value")

    if pre != "did" or meth != method:
        raise ValueError("Invalid DID value")

    return (did, index, keystr)

def extractDidSignerParts(signer, method="igo"):
    """
    Parses and returns did index keystr from signer key indexed did
    as tuple (did, index, keystr)
    raises ValueError if fails parsing
    """
    # get signer key from read data. assumes that resource is valid
    try:
        did, index = signer.rsplit("#", maxsplit=1)
        index = int(index)  # get index and sdid from signer field
    except ValueError as ex:
        raise ValueError("Invalid indexed signer value")

    try:  # correct did format  pre:method:keystr
        pre, meth, keystr = did.split(":")
    except ValueError as ex:
        raise ValueError("Malformed DID value")

    if pre != "did" or meth != method:
        raise ValueError("Invalid DID value")

    return (did, index, keystr)

def extractDidParts(did, method="igo"):
    """
    Parses and returns keystr from did
    raises ValueError if fails parsing
    """
    try:  # correct did format  pre:method:keystr
        pre, meth, keystr = did.split(":")
    except ValueError as ex:
        raise ValueError("Malformed DID value")

    if pre != "did" or meth != method:
        raise ValueError("Invalid DID value")

    return keystr


def makeSignedAgentReg(vk, sk, changed=None, **kwa):
    """
    Return duple of (signature,registration) of minimal self-signing
    agent registration record for keypair vk, sk

    registration is json encoded unicode string of registration record
    signature is base64 url-file safe unicode string signature generated
    by signing bytes version of registration

    Parameters:
        vk is bytes that is the public verification key
        sk is bytes that is the private signing key
        changed is ISO8601 date time stamp string if not provided then uses current datetime
        **kwa are optional fields to be added to data resource. Each keyword is
           the associated field name and the argument parameter is the value of
           that field in the data resource.  Keywords in ("did", "signer", "changed",
            "keys") will be overidden. Common use case is "issuants".


    """
    reg = ODict(did="", signer="", changed="", keys=None)  # create registration record as dict
    if kwa:
        reg.update(kwa.items())

    if not changed:
        changed = timing.iso8601(aware=True)

    did = makeDid(vk)  # create the did
    index = 0
    signer = "{}#{}".format(did, index)  # signer field value key at index
    key64u = keyToKey64u(vk)  # make key index field value
    kind = "EdDSA"

    reg["did"] = did
    reg["signer"] = signer
    reg["changed"] = changed
    reg["keys"] = [ODict(key=key64u, kind=kind)]

    registration = json.dumps(reg, indent=2)
    sig = libnacl.crypto_sign(registration.encode("utf-8"), sk)[:libnacl.crypto_sign_BYTES]
    signature = keyToKey64u(sig)

    return (signature, registration)

def validateSignedAgentReg(signature, registration, method="igo"):
    """
    Returns dict of deserialized registration if signature verifies
    and registration is correctly formed with self-signing did-key
    Otherwise returns None

    signature is base64 url-file safe unicode string signature generated
    by signing bytes version of registration

    registration is json encoded unicode string of registration record

    method is the method string used to generate dids in the registration
    """
    try:
        try:
            reg = json.loads(registration, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not reg:  # registration must not be empty
            return None

        if not isinstance(reg, dict):  # must be dict subclass
            return None

        if "changed" not in reg:  # changed field required
            return None

        try:
            arrow.get(reg["changed"])
        except arrow.parser.ParserError as ex:  # invalid datetime format
            return None

        if "signer" not in reg:  # signer field required
            return None

        try:
            sdid, index = reg["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (KeyError, ValueError) as ex:
            return None  # missing sdid or index

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = sdid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        if "did" not in reg:  # did field required
            return None

        if reg['did'] != sdid:
            return None  # must be self signing and same key in signer

        if "keys" not in reg:  # must have key field
            return None

        try:
            keyer = reg["keys"][index]
        except IndexError as ex:
            return None  # missing index

        if "key" not in keyer:  # missing key
            return None

        if "kind" not in keyer:  # missing kind
            return None

        kind = keyer["kind"]

        if kind not in ("EdDSA", "Ed25519"):
            return None  # invalid key kind

        verkey = keyer["key"]

        if verkey != keystr:
            return None  # must be same key that created did and signer

        if len(verkey) != 44:
            return None  # invalid length for base64 encoded key

        if not verify64u(signature, registration, verkey):
            return None  # signature fails

    except Exception as ex:  # unknown problem
        return None

    return reg

def makeSignedThingReg(dvk, dsk, ssk, signer, changed=None, hid=None, **kwa):
    """
    Return triple of (dsignature, ssignature, registration) of minimal self-signing
    thing registration record for did keypair (dvk, dsk) and signer key ssk as well
    as signer key indexed did signer and hid

    dsignature is base64 url-file safe unicode string signature generated
        by signing bytes version of registration with dsk
    ssignature is base64 url-file safe unicode string signature generated
        by signing bytes version of registration with ssk
    registration is json encoded unicode string of registration record
        {
          "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
          "hid": "hid:dns:canon.com#01,
          "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
          "changed": "2000-01-01T00:00:00+00:00",
          "data":
          {
            "keywords": ["Canon", "EOS Rebel T6", "251440"],
            "message": "If found call this number",
          }
        }

    Parameters:
        dvk is bytes that is the public verification key for the thing did
        dsk is bytes that is the private signing key for dvk
        ssk is bytes that is the private signing key indicated by
            the signer key indexed did
        signer is key indexed did to the key of the signer Agent that controls the thing
            svk, ssk, and signer are for the same keypair
        changed is optional ISO8601 date time stamp string
            if not provided then uses current datetime
        hid is optional HID for the thing that is controlled by signer/issuer  Agent
            if provided hid must validate as being controlled by signer/issuer Agent
        **kwa are optional fields to be added to data resource. Each keyword is
           the associated field name and the argument parameter is the value of
           that field in the data resource.  Keywords in ("did", "signer", "changed",
            "keys", "hid") will be overidden. Common use case is data.

    """
    reg = ODict(did="", hid="", signer="", changed="")  # create registration record as dict
    if kwa:
        reg.update(kwa.items())

    if not changed:
        changed = timing.iso8601(aware=True)

    tdid = makeDid(dvk)  # create the thing did
    reg["did"] = tdid

    if hid is not None:
        reg["hid"] = hid

    reg["signer"] = signer
    reg["changed"] = changed

    registration = json.dumps(reg, indent=2)

    dsig = libnacl.crypto_sign(registration.encode("utf-8"), dsk)[:libnacl.crypto_sign_BYTES]
    dsignature = keyToKey64u(dsig)

    ssig = libnacl.crypto_sign(registration.encode("utf-8"), ssk)[:libnacl.crypto_sign_BYTES]
    ssignature = keyToKey64u(ssig)

    return (dsignature, ssignature, registration)


def validateSignedThingReg(signature, registration, method="igo"):
    """
    Returns dict of deserialized registration if signature
    verifies and registration is correctly formed. The registration must also
    verify with the signer's signature using validateSignedResource for a
    complete validation.

    Otherwise returns None

    signature is base64 url-file safe unicode string signature generated
        by signing bytes version of registration with privated signing key associated with
        public verification key used to create did in registration

    registration is json encoded unicode string of registration record

    method is the method string used to generate dids in the registration
    """

    try:
        try:
            reg = json.loads(registration, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not reg:  # registration must not be empty
            return None

        if not isinstance(reg, dict):  # must be dict subclass
            return None

        if "changed" not in reg:  # changed field required
            return None

        try:
            arrow.get(reg["changed"])
        except arrow.parser.ParserError as ex:  # invalid datetime format
            return None

        if "signer" not in reg:  # signer field required
            return None

        try:
            sdid, index = reg["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (KeyError, ValueError) as ex:
            return None  # missing sdid or index

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = sdid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        if "hid" not in reg:  # hid field required
            return None

        if "did" not in reg:  # did field required
            return None

        ddid = reg["did"]

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = ddid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        verkey = keystr

        if len(verkey) != 44:
            return None  # invalid length for base64 encoded key

        if not verify64u(signature, registration, verkey):
            return None  # signature fails

    except Exception as ex:  # unknown problem
        return None

    return reg

def validateSignedResource(signature, resource, verkey, method="igo"):
    """
    Returns dict of deserialized resource if signature verifies for resource given
    verification key verkey in base64 url safe unicode format
    Otherwise returns None


    signature is base64 url-file safe unicode string signature generated
        by signing bytes version of resource with privated signing key associated with
        public verification key referenced by key indexed signer field in resource

    resource is json encoded unicode string of resource record

    verkey is base64 url-file safe unicode string public verification key referenced
        by signer field in resource. This is looked up in database from signer's
        agent data resource

    method is the method string used to generate dids in the resource
    """

    try:
        try:
            rsrc = json.loads(resource, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not rsrc:  # resource must not be empty
            return None

        if not isinstance(rsrc, dict):  # must be dict subclass
            return None

        if "changed" not in rsrc:  # changed field required
            return None

        try:
            arrow.get(rsrc["changed"])
        except arrow.parser.ParserError as ex:  # invalid datetime format
            return None

        if "signer" not in rsrc:  # signer field required
            return None

        try:
            sdid, index = rsrc["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (AttributeError, ValueError) as ex:
            return None  # missing sdid or index

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = sdid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        if "did" not in rsrc:  # did field required
            return None

        ddid = rsrc["did"]

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = ddid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        if len(verkey) != 44:
            return None  # invalid length for base64 encoded key

        if not verify64u(signature, resource, verkey):
            return None  # signature fails

    except Exception as ex:  # unknown problem
        return None

    return rsrc


def validateSignedAgentWrite(cdat, csig, sig, ser,  method="igo"):
    """
    Returns deserialized version of serialization ser which is resource to be written
    if signature sig verifies and resource is correctly formed.
    Otherwise returns None

    cdat is current record dict in database

    csig is signature using current signer field in resource to be overwritten

    sig is base64 url-file safe unicode string signature generated
        by signing bytes version of registration with new privated signing key
        associated with public verification key in signer field in updated resourse

    ser is json encoded unicode string of registration record



    method is the method string used to generate dids in the registration
    """

    try:

        # get signer key from read data. assumes that resource is valid
        try:
            cdid, index = cdat["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (KeyError, ValueError) as ex:
            return None  # missing sdid or index

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = cdid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        cverkey = keystr  # existing resources verify key

        # verify request using existing resources signer verify key
        if not verify64u(csig, ser, cverkey):
            return None  # signature fails

        # now validate updated resource
        try:
            dat = json.loads(ser, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not dat:  # registration must not be empty
            return None

        if not isinstance(dat, dict):  # must be dict subclass
            return None

        if "changed" not in dat:  # changed field required
            return None

        try:
            dt = arrow.get(dat["changed"])
        except arrow.parser.ParserError as ex:  # invalid datetime format
            return None

        # Compare changed
        cdt = arrow.get(cdat["changed"])
        if dt <= cdt:  # not later
            return None

        if "signer" not in dat:  # signer field required
            return None

        try:
            sdid, index = dat["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (AttributeError, ValueError) as ex:
            return None  # missing sdid or index

        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = sdid.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        if "did" not in dat:  # did field required
            return None

        if dat['did'] != sdid:  # not self signed
            return None

        if sdid != cdid:  # not same resource
            return None

        try:
            verkey = dat['keys'][index]['key']
        except (TypeError, KeyError, IndexError) as ex:
            return None

        if len(verkey) != 44:
            return None  # invalid length for base64 encoded key

        if not verify64u(sig, ser, verkey):  # verify with new signer verify key
            return None  # signature fails

    except Exception as ex:  # unknown problem
        return None

    return dat


def validateSignedThingWrite(sdat, cdat, csig, sig, ser,  method="igo"):
    """
    Returns deserialized version of serialization ser which is resource to be written
    if signature sig verifies and resource is correctly formed.
    Otherwise returns None

    sdat is current signer dict converted from database

    cdat is current record dict converted from database

    csig is signature using current signer field in resource to be overwritten

    sig is base64 url-file safe unicode string signature generated
        by signing bytes version of registration with new privated signing key
        associated with public verification key in signer field in updated resourse

    ser is json encoded unicode string of registration record



    method is the method string used to generate dids in the registration
    """

    try:
        # get signer key index from signer field in cdat
        try:
            (sdid, index, akey) = extractDatSignerParts(cdat)
        except ValueError as ex:
            return None

        # get signer key from signer data. assumes that resource is valid
        try:
            sverkey = sdat["keys"][index]["key"]
        except (TypeError, KeyError, IndexError) as ex:
            return None

        if len(sverkey) != 44:
            return None  # invalid length for base64 encoded key

        # verify request using existing resources signer verify key
        if not verify64u(csig, ser, sverkey):
            return None  # signature fails

        # now validate updated resource
        try:
            dat = json.loads(ser, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not dat:  # registration must not be empty
            return None

        if not isinstance(dat, dict):  # must be dict subclass
            return None

        if "changed" not in dat:  # changed field required
            return None

        try:
            dt = arrow.get(dat["changed"])
        except arrow.parser.ParserError as ex:  # invalid datetime format
            return None

        # Compare changed
        cdt = arrow.get(cdat["changed"])
        if dt <= cdt:  # not later
            return None

        if "did" not in dat:  # did field required
            return None

        if dat['did'] != cdat['did']:  # not same resource
            return None

        # validate new signer
        try:
            (sdid, nindex, akey) = extractDatSignerParts(dat)
        except ValueError as ex:
            return None

        try:
            nverkey = sdat['keys'][nindex]['key']  # new index
        except (KeyError, IndexError) as ex:
            return None

        if len(nverkey) != 44:
            return None  # invalid length for base64 encoded key

        if not verify64u(sig, ser, nverkey):  # verify with new signer verify key
            return None  # signature fails

    except Exception as ex:  # unknown problem
        return None

    return dat


def validateMessageData(ser):
    """
    Returns deserialized version of serialization ser which is message to be written
    if message is correctly formed.
    Otherwise returns None

    ser is json encoded unicode string of message
    """

    try:
        # now validate message data
        try:
            dat = json.loads(ser, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not dat:  # registration must not be empty
            return None

        if not isinstance(dat, dict):  # must be dict subclass
            return None

        requireds = ("uid", "kind", "signer", "date", "to", "from", "subject", "content")
        for field in requireds:
            if field not in dat:
                return None

        try:
            dt = arrow.get(dat["date"])
        except arrow.parser.ParserError as ex:  # invalid datetime format
            return None

    except Exception as ex:  # unknown problem
        return None

    return dat


def verifySignedMessageWrite(sdat, index, sig, ser):
    """
    Returns True
    If signature sig verifies with serialization ser with key at index in
    signer sdat.
    Otherwise returns False

    sdat is current signer dict converted from database

    index is index of key in signer data sdat

    sig is signature using current signer field

    ser is json encoded unicode string of message
    """
    try:
        # get signer key at index from signer data. assumes that resource is valid
        try:
            sverkey = sdat["keys"][index]["key"]
        except (TypeError, KeyError, IndexError) as ex:
            return False

        if len(sverkey) != 44:
            return False  # invalid length for base64 encoded key

        # verify request using existing resources signer verify key
        if not verify64u(sig, ser, sverkey):
            return False  # signature fails

    except Exception as ex:  # unknown problem
        return False

    return True

def validateSignedOfferData(adat, ser, sig, tdat, method="igo"):
    """
    Returns deserialized version of serialization ser which Offer
        if offer request is correctly formed.
    Otherwise returns None

    adat is thing's holder/owner agent resource
    ser is json encoded unicode string of request
    sig is base64 encoded signature from request header "signer" tag
    tdat is thing data resource

    offer request fields
    {
        "uid": offeruniqueid,
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
    }

    """
    try:

        try:  # get signing key of request from thing resource
            (adid, index, akey) = extractDatSignerParts(tdat)
        except ValueError as ex:
            return None

        # get agent key at index from signer data. assumes that resource is valid
        try:
            averkey = adat["keys"][index]["key"]
        except (TypeError, KeyError, IndexError) as ex:
            return None

        if len(averkey) != 44:
            return None  # invalid length for base64 encoded key

        # verify request using agent signer verify key
        if not verify64u(sig, ser, averkey):
            return None  # signature fails
        # now validate offer data
        try:
            dat = json.loads(ser, object_pairs_hook=ODict)
        except ValueError as ex:
            return None  # invalid json

        if not dat:  # offer request must not be empty
            return None

        if not isinstance(dat, dict):  # must be dict subclass
            return None

        requireds = ("uid", "thing", "aspirant", "duration")
        for field in requireds:
            if field not in dat:
                return None

        if not dat["uid"]:  # uid must not be empty
            return None

        if dat["thing"] != tdat['did']:
            return None

        aspirant = dat["aspirant"]
        try:  # correct did format  pre:method:keystr
            pre, meth, keystr = aspirant.split(":")
        except ValueError as ex:
            return None

        if pre != "did" or meth != method:
            return None  # did format bad

        try:
            duration = float(dat["duration"])
        except ValueError as ex:
            return None

        if duration <= PROPAGATION_DELAY * 2.0:
            return None

    except Exception as ex:  # unknown problem
        return None

    return dat



def buildSignedServerOffer(dat, ser, sig, sdat, dt, sk, **kwa):
    """
    Return triple of (odat, oser, osig)

    Where:
       odat is server offer dict data
       oser is JSON serialize version of oser
       osig is signature base64U using sk

    Parameters:
       dat is offer request dat
       ser is offer request JSON serialization
       sig is offer request signature
       sdat is server resource
       dt is current datetime
       sk is server private signing key

    registration is json encoded unicode string of registration record
    signature is base64 url-file safe unicode string signature generated
    by signing bytes version of registration

    Parameters:
        vk is bytes that is the public verification key
        sk is bytes that is the private signing key
        changed is ISO8601 date time stamp string if not provided then uses current datetime
        **kwa are optional fields to be added to data resource. Each keyword is
           the associated field name and the argument parameter is the value of
           that field in the data resource.  Keywords in ("did", "signer", "changed",
            "keys") will be overidden. Common use case is "issuants".

      offer request fields
    {
        "uid": offeruniqueid,
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
    }

    offer response fields
    {
        "uid": offeruniqueid,
        "thing": thingDID,
        "aspirant": AgentDID,
        "duration": timeinsecondsofferisopen,
        "expiration": datetimeofexpiration,
        "signer": serverkeydid,
        "offerer": ownerkeydid,
        "offer": Base64serrequest
    }
    """
    duration = float(dat["duration"])
    odat = ODict()
    if kwa:
        odat.update(kwa.items())

    odat["uid"] = dat["uid"]
    odat["thing"] = dat["thing"]
    odat["aspirant"] = dat["aspirant"]
    odat["duration"] = duration

    td = datetime.timedelta(seconds=duration)
    odat["expiration"] = timing.iso8601(dt + td, aware=True)
    odat["signer"] = sdat["signer"]   # assumes sk and sdat["signer"] correspond
    odat["offerer"] = tdat["signer"]
    odat["offer"] = keyToKey64u(ser.encode("utf-8"))

    oser = json.dumps(odat, indent=2)
    osig = keyToKey64u(libnacl.crypto_sign(registration.encode("utf-8"), sk)[:libnacl.crypto_sign_BYTES])

    return (odat, oser, osig)
