# -*- encoding: utf-8 -*-
"""
Ending Module

ReST endpoints

"""
from __future__ import generator_stop

from collections import OrderedDict as ODict, deque
import enum
try:
    import simplejson as json
except ImportError:
    import json

import datetime

import arrow
import falcon
import libnacl

from ioflo.aid.sixing import *
from ioflo.aid import lodict
from ioflo.aid import timing
from ioflo.aid import classing
from ioflo.aio.http import httping

from ioflo.aid import getConsole

from ..bluepeaing import SEPARATOR, TRACK_EXPIRATION_DELAY, ValidationError

from ..help.helping import (parseSignatureHeader, verify64u, extractDidParts,
                            extractDatSignerParts, extractDidSignerParts,
                            validateSignedAgentReg, validateSignedThingReg,
                            validateSignedResource, validateSignedAgentWrite,
                            validateSignedThingWrite, keyToKey64u,
                            validateMessageData, verifySignedMessageWrite,
                            validateSignedOfferData, buildSignedServerOffer,
                            validateSignedThingTransfer, validateAnon,
                            validateIssuerDomainGen, )
from ..db import dbing
from ..keep import keeping

console = getConsole()

AGENT_BASE_PATH = "/agent"
SERVER_BASE_PATH = "/server"
THING_BASE_PATH = "/thing"
ANON_MSG_BASE_PATH = "/anon"
DEMO_BASE_PATH = "/demo"

class ServerResource:
    """
    Server Agent Resource

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    def on_get(self, req, rep):
        """
        Handles GET request for the Server Agent
        """
        did = keeping.gKeeper.did

        # read from database
        try:
            dat, ser, sig = dbing.getSelfSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser


class AgentResource:
    """
    Agent Resource

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    @classing.attributize
    def onPostGen(self, skin, req, rep):
        """
        Generator to perform Agent post with support for backend request
        to validate issuant (HID)

        attributes:
        skin._status
        skin._headers

        are special and if assigned inside generator used by WSGI server
        to update status and headers upon first non-empty write.
        Does not use self. because only one instance of resource is used
        to process all requests.


        response = odict([('version', self.respondent.version),
                            ('status', self.respondent.status),
                            ('reason', self.respondent.reason),
                            ('headers', copy.copy(self.respondent.headers)),
                            ('body', self.respondent.body),
                            ('data', self.respondent.data),
                            ('request', request),
                            ('errored', self.respondent.errored),
                            ('error', self.respondent.error),
                           ])

        {'check': 'did|issuer|date',
        'signer': 'did#index'}
        """
        skin._status = None  # used to update status in iterator if not None
        skin._headers = lodict()  # used to update headers in iterator if not empty
        yield b''  # ensure its a generator

        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)
        sig = sigs.get('signer')  # str not bytes
        if not sig:
            raise fhttping.HTTPError(httping.BAD_REQUEST,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                       'Read Error',
                                       'Could not read the request body.')

        ser = serb.decode("utf-8")

        try:
            dat = validateSignedAgentReg(sig, ser)
        except ValidationError as ex:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                    'Validation Error',
                                    'Error validating the request body. {}'.format(ex))

        did = dat['did']  # unicode version

        if "issuants" in dat:  # validate hid control here
            for issuant in dat["issuants"]:
                try:
                    result = yield from validateIssuerDomainGen(self.store,
                                                                dat,
                                                                issuant,
                                                                timeout=0.5)  # raises  error if fails
                except ValidationError as ex:
                    raise httping.HTTPError(httping.BAD_REQUEST,
                                        'Validation Error',
                                        'Error validating issuant. {}'.format(ex))

        # no error so save to database
        try:
            dbing.putSigned(key=did, ser=ser, sig=sig, clobber=False)
        except dbing.DatabaseError as ex:
            raise httping.HTTPError(httping.PRECONDITION_FAILED,
                                       'Database Error',
                                      '{}'.format(ex.args[0]))

        skin._status = httping.CREATED
        didURI = falcon.uri.encode_value(did)
        skin._headers["Location"] = "{}?did={}".format(AGENT_BASE_PATH, didURI)
        # normally picks of content-type from type of request but set anyway to ensure
        skin._headers["Content-Type"] = "application/json; charset=UTF-8"

        body = json.dumps(dat, indent=2).encode()
        # inside rep.stream generator, body is yielded or returned, not assigned to rep.body
        return body


    def on_post(self, req, rep):
        """
        Handles POST requests
        """
        rep.stream = self.onPostGen(req, rep)  # iterate on stream generator

    def on_get(self, req, rep):
        """
        Handles GET request for an AgentResources given by query parameter
        with did


        """
        did = req.get_param("did")  # already has url-decoded query parameter value
        if not did:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Query Parameter Error',
                                    'Missing query did. {}')

        # read from database
        try:
            dat, ser, sig = dbing.getSelfSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser


class AgentDidResource:
    """
    Agent Did Resource
    Access agent by DID

    /agent/{adid}

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    @classing.attributize
    def onPutGen(self, skin, req, rep, did):
        """
        Generator to perform Agent put with support for backend request
        to validate issuant (HID)

        attributes:
        skin._status
        skin._headers

        are special and if assigned inside generator used by WSGI server
        to update status and headers upon first non-empty write.
        Does not use self. because only one instance of resource is used
        to process all requests.
        """
        skin._status = None  # used to update status in iterator if not None
        skin._headers = lodict()  # used to update headers in iterator if not empty
        yield b''  # ensure its a generator

        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)
        sig = sigs.get('signer')  # str not bytes
        if not sig:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')
        csig = sigs.get('current')  # str not bytes
        if not csig:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                       'Read Error',
                                       'Could not read the request body.')
        ser = serb.decode("utf-8")

        # Get validated current resource from database
        try:
            rdat, rser, rsig = dbing.getSelfSigned(did)
        except dbing.DatabaseError as ex:
            raise httping.HTTPError(httping.BAD_REQUEST,
                            'Resource Verification Error',
                            'Error verifying signer resource. {}'.format(ex))

        # validate request
        try:
            dat = validateSignedAgentWrite(cdat=rdat, csig=csig, sig=sig, ser=ser)
        except ValidationError as ex:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                               'Validation Error',
                            'Error validating the request body. {}'.format(ex))

        if "issuants" in dat:  # validate hid control here
            for issuant in dat["issuants"]:
                try:
                    result = yield from validateIssuerDomainGen(self.store,
                                                                dat,
                                                                issuant,
                                                                timeout=0.5)  # raises  error if fails
                except ValidationError as ex:
                    raise httping.HTTPError(httping.BAD_REQUEST,
                                        'Validation Error',
                                        'Error validating issuant. {}'.format(ex))

        # save to database
        try:
            dbing.putSigned(key=did, ser=ser, sig=sig,  clobber=True)
        except dbing.DatabaseError as ex:
            raise httping.HTTPError(httping.PRECONDITION_FAILED,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))


        # normally picks of content-type from type of request but set anyway to ensure
        skin._headers["Content-Type"] = "application/json; charset=UTF-8"
        skin._headers["Signature"] = 'signer="{}"'.format(sig)

        skin._status = httping.OK
        # inside rep.stream generator, body is yielded or returned, not assigned to rep.body
        return ser.encode()


    def on_put(self, req, rep, did):
        """
        Handles PUT requests

        /agent/{did}

        Falcon url decodes path parameters such as {did}
        """
        rep.stream = self.onPutGen(req, rep, did)  # iterate on stream generator


    def on_get(self, req, rep, did):
        """
        Handles GET request for an Agent Resource by did

        /agent/{did}

        Falcon url decodes path parameters such as {did}
        """
        # read from database
        try:
            dat, ser, sig = dbing.getSelfSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser

class AgentDidDropResource:
    """
    Agent Did  Drop Resource
    Drop message in inbox of Agent

    /agent/{did}/drop

    did is receiver agent  did


    Attributes:
        .store is reference to ioflo data store

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
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    def on_post(self, req, rep, did):
        """
        Handles POST requests
        """
        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)
        msig = sigs.get('signer')  # str not bytes
        if not msig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            mserb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                       'Could not read the request body.')

        mser = mserb.decode("utf-8")
        try:
            mdat = validateMessageData(mser)
        except ValidationError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Validation Error',
                                    'Invalid message data. {}'.format(ex))

        if did != mdat['to']:  # destination to did and did in url not same
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Validation Error',
                                    'Mismatch message to and url DIDs.')


        # extract sdid and keystr from signer field in message
        try:
            (sdid, index, akey) = extractDatSignerParts(mdat)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                'Missing or Invalid signer field. {}'.format(ex))

        # Get validated signer resource from database
        try:
            sdat, sser, ssig = dbing.getSelfSigned(sdid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                    'Error verifying signer resource. {}'.format(ex))

        # verify request signature
        try:
            result = verifySignedMessageWrite(sdat=sdat, index=index, sig=msig, ser=mser)
        except ValidationError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Validation Error',
                            'Error validating the request body. {}'.format(ex))

        if sdid != mdat['from']:  # destination to did and did in url not same
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Validation Error',
                                    'Mismatch message from and signer DIDs.')

        # Get validated destination agent resource from database
        try:
            ddat, dser, dsig = dbing.getSelfSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                    'Error verifying destination resource. {}'.format(ex))

        # Build key for message from (to, from, uid)  (did, sdid, uid)
        muid = mdat['uid']
        key = "{}/drop/{}/{}".format(did, sdid, muid)

        # save message to database error if duplicate
        try:
            dbing.putSigned(key=key, ser=mser, sig=msig, clobber=False)  # no clobber so error
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))



        didUri = falcon.uri.encode_value(did)
        sdidUri = falcon.uri.encode_value(sdid)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}/{}/drop?from={}&uid={}".format(AGENT_BASE_PATH,
                                                          didUri,
                                                          sdidUri,
                                                          muid)
        rep.body = json.dumps(mdat, indent=2)

    def on_get(self, req, rep, did):
        """
        Handles GET request for an AgentResources given by query parameter
        with did


        """
        muid = req.get_param("uid") # returns url-decoded query parameter value
        sdid = req.get_param("from")  # returns url-decoded query parameter value
        index = req.get_param("index")  # returns url-decoded query parameter value

        if index is not None:
            try:
                index = int(index)
            except (ValueError, TypeError) as  ex:
                raise falcon.HTTPError(falcon.HTTP_400,
                                       'Request Error',
                                       'Invalid request format. {}'.format(ex))


        key = "{}/drop/{}/{}".format(did, sdid, muid)

        # read from database
        try:
            dat, ser, sig = dbing.getSigned(key)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser


class ThingResource:
    """
    Thing Resource

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    @classing.attributize
    def onPostGen(self, skin, req, rep):
        """
        Generator to perform Thing post with support for backend request
        to validate issuant (HID)

        attributes:
        skin._status
        skin._headers

        are special and if assigned inside generator used by WSGI server
        to update status and headers upon first non-empty write.
        Does not use self. because only one instance of resource is used
        to process all requests.
        """
        skin._status = None  # used to update status in iterator if not None
        skin._headers = lodict()  # used to update headers in iterator if not empty
        yield b''  # ensure its a generator

        sigs = parseSignatureHeader(req.get_header("Signature"))

        dsig = sigs.get('did')  # str not bytes thing's did signature
        if not dsig:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        tsig = sigs.get('signer')  # str not bytes thing's signer signature
        if not tsig:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                       'Read Error',
                                       'Could not read the request body.')

        ser = serb.decode("utf-8")

        # validate thing resource and verify did signature
        try:
            dat = validateSignedThingReg(dsig, ser)
        except ValidationError as ex:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                           'Validation Error',
                            'Could not validate the request body. {}'.format(ex))

        # verify signer signature by looking up signer data resource in database
        try:
            sdid, index = dat["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (AttributeError, ValueError) as ex:
                raise httping.HTTPError(httping.BAD_REQUEST,
                                   'Validation Error',
                                    'Invalid or missing did key index.')   # missing sdid or index

        # read and verify signer agent from database
        try:
            sdat, sser, ssig = dbing.getSelfSigned(sdid)
        except dbing.DatabaseError as ex:
            raise httping.HTTPError(httping.BAD_REQUEST,
                            'Resource Verification Error',
                            'Error verifying signer resource. {}'.format(ex))

        # now use signer agents key indexed for thing signer to verify thing resource
        try:
            tkey = sdat['keys'][index]['key']
        except (TypeError, IndexError, KeyError) as ex:
            raise httping.HTTPError(httping.FAILED_DEPENDENCY,
                                           'Data Resource Error',
                                           'Missing signing key')
        try:
            validateSignedResource(tsig, ser, tkey)
        except ValidationError as ex:
            raise httping.HTTPError(httping.BAD_REQUEST,
                                   'Validation Error',
                        'Could not validate the request body. {}'.format(ex))

        tdid = dat['did']  # unicode version

        if "hid" in dat and dat["hid"]:  # non-empty hid
            # validate hid control here
            found = False
            for issuant in sdat.get("issuants", []):
                issuer = issuant.get("issuer")
                try:
                    prefix, kind, issue = dat['hid'].split(":", maxsplit=2)
                except ValueError as ex:
                    raise httping.HTTPError(httping.BAD_REQUEST,
                                                    'Validation Error',
                                        'Invalid hid format. {}'.format(ex))
                if issue.startswith(issuer):
                    found = True
                    try:
                        result = yield from validateIssuerDomainGen(self.store,
                                                                    sdat,
                                                                    issuant,
                                                                    timeout=0.5)  # raises  error if fails
                    except ValidationError as ex:
                        raise httping.HTTPError(httping.BAD_REQUEST,
                                            'Validation Error',
                                            'Error validating issuant. {}'.format(ex))

                    try:  # add entry to hids table to lookup did by hid
                        dbing.putHid(dat['hid'], tdid)
                    except DatabaseError as ex:
                        raise httping.HTTPError(httping.PRECONDITION_FAILED,
                                              'Database Error',
                                              '{}'.format(ex.args[0]))

            if not found:
                raise httping.HTTPError(httping.FAILED_DEPENDENCY,
                                                    'Validation Error',
                            'Controlling Agent does not corresponding issuant')

        # save to database core
        try:
            dbing.putSigned(key=tdid, ser=ser, sig=tsig, clobber=False)
        except dbing.DatabaseError as ex:
            raise httping.HTTPError(httping.PRECONDITION_FAILED,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))

        skin._status = httping.CREATED
        didURI = falcon.uri.encode_value(tdid)
        skin._headers["Location"] = "{}?did={}".format(THING_BASE_PATH, didURI)
        # normally picks of content-type from type of request but set anyway to ensure
        skin._headers["Content-Type"] = "application/json; charset=UTF-8"

        body = json.dumps(dat, indent=2).encode()
        # inside rep.stream generator, body is yielded or returned, not assigned to rep.body
        return body


    def on_post(self, req, rep):
        """
        Handles POST requests
        """
        rep.stream = self.onPostGen(req, rep)  # iterate on stream generator


    def on_get(self, req, rep):
        """
        Handles GET request for an ThingResources given by query parameter
        with did

        """
        did = req.get_param("did")  # already has url-decoded query parameter value
        #didb = did.encode("utf-8")  # bytes version

        # read from database
        try:
            dat, ser, sig = dbing.getSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        if dat is None:
            raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                                               'Not Found Error',
                                               'DID resource does not exist')

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser

class ThingDidResource:
    """
    Thing Did Resource
    Access Thing resource by DID

    /thing/{did}

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    @classing.attributize
    def onPutGen(self, skin, req, rep, did):
        """
        Generator to perform Agent put with support for backend request
        to validate issuant (HID)

        attributes:
        skin._status
        skin._headers

        are special and if assigned inside generator used by WSGI server
        to update status and headers upon first non-empty write.
        Does not use self. because only one instance of resource is used
        to process all requests.
        """
        skin._status = None  # used to update status in iterator if not None
        skin._headers = lodict()  # used to update headers in iterator if not empty
        yield b''  # ensure its a generator

        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)
        sig = sigs.get('signer')  # str not bytes
        if not sig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Validation Error',
                                               'Invalid or missing Signature header.')
        csig = sigs.get('current')  # str not bytes
        if not csig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Validation Error',
                                               'Invalid or missing Signature header.')

        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                           'Could not read the request body.')
        ser = serb.decode("utf-8")

        try:  # validate did
            ckey = extractDidParts(did)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                               'Invalid did field. {}'.format(ex))


        try: # Get validated existing resource from database
            cdat, cser, psig = dbing.getSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                'Error verifying current thing resource. {}'.format(ex))

        # extract sdid and keystr from signer field
        try:
            (sdid, index, akey) = extractDatSignerParts(cdat)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                               'Missing or Invalid signer field. {}'.format(ex))

        # Get validated signer resource from database
        try:
            sdat, sser, ssig = dbing.getSelfSigned(sdid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                           'Error verifying signer resource. {}'.format(ex))

        # validate request
        try:
            dat = validateSignedThingWrite(sdat=sdat, cdat=cdat, csig=csig, sig=sig, ser=ser)
        except ValidationError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Validation Error',
                                                   'Error validating the request body. {}'.format(ex))

        if "hid" in dat:  # new or changed hid
            if ((dat["hid"] and not "hid" in cdat) or
                    (dat["hid"] and dat["hid"] != cdat["hid"])):
                # validate hid control here
                found = False
                for issuant in sdat.get("issuants", []):
                    issuer = issuant.get("issuer")
                    try:
                        prefix, kind, issue = dat['hid'].split(":", maxsplit=2)
                    except ValueError as ex:
                        raise httping.HTTPError(httping.BAD_REQUEST,
                                                        'Validation Error',
                                            'Invalid hid format. {}'.format(ex))
                    if issue.startswith(issuer):
                        found = True
                        try:
                            result = yield from validateIssuerDomainGen(self.store,
                                                                        sdat,
                                                                        issuant,
                                                                        timeout=0.5)  # raises  error if fails
                        except ValidationError as ex:
                            raise httping.HTTPError(httping.BAD_REQUEST,
                                                'Validation Error',
                                                'Error validating issuant. {}'.format(ex))

                        try:  # add entry to hids table to lookup did by hid
                            dbing.putHid(dat['hid'], did)
                        except DatabaseError as ex:
                            raise httping.HTTPError(httping.PRECONDITION_FAILED,
                                                  'Database Error',
                                                  '{}'.format(ex.args[0]))

                if not found:
                    raise httping.HTTPError(httping.FAILED_DEPENDENCY,
                                                        'Validation Error',
                                'Controlling Agent does not corresponding issuant')
        if ("hid" in cdat and cdat["hid"] and
                (not "hid" in dat or dat["hid"] != cdat["hid"])):
            try:  # put empty in old cdat hid entry
                dbing.putHid(cdat['hid'], "")
            except DatabaseError as ex:
                raise httping.HTTPError(httping.PRECONDITION_FAILED,
                                      'Database Error',
                                      '{}'.format(ex.args[0]))

        try:  # save to database
            dbing.putSigned(key=did, ser=ser, sig=sig, clobber=True)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                       'Database Error',
                                      '{}'.format(ex.args[0]))

        # normally picks of content-type from type of request but set anyway to ensure
        skin._headers["Content-Type"] = "application/json; charset=UTF-8"
        skin._headers["Signature"] = 'signer="{}"'.format(sig)

        skin._status = httping.OK
        # inside rep.stream generator, body is yielded or returned, not assigned to rep.body
        return ser.encode()

    def on_put(self, req, rep, did):
        """
        Handles PUT requests

        /thing/{did}

        Falcon url decodes path parameters such as {did}
        """
        rep.stream = self.onPutGen(req, rep, did)  # iterate on stream generator

    def on_get(self, req, rep, did):
        """
        Handles GET request for an Thing Resource by did

        /thing/{did}

        Falcon url decodes path parameters such as {did}
        """
        # read from database
        try:
            dat, ser, sig = dbing.getSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        if dat is None:
            raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                                               'Not Found Error',
                                               'DID resource does not exist')

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser

class ThingDidOfferResource:
    """
    Thing Did Offer Resource
    Create offer to transfer title to Thing at DID message

    /thing/{did}/offer

    did is thing did

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

    The value of the did to offer expires entry
    {
        "offer": "{did}/offer/{ouid}",  # key of offer entry in core database
        "expire": "2000-01-01T00:36:00+00:00", #  ISO-8601 expiration date of offer
    }

    Database key is
    did/offer/ouid

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    def on_post(self, req, rep, did):
        """
        Handles POST requests
        """
        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)
        sig = sigs.get('signer')  # str not bytes
        if not sig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                       'Could not read the request body.')

        try:  # validate did
            tkey = extractDidParts(did)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Resource Verification Error',
                                           'Invalid did field. {}'.format(ex))

        try:  # Get validated thing resource from database
            tdat, tser, tsig = dbing.getSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                    'Error verifying signer resource. {}'.format(ex))


        try:  # validate signer field
            (adid, index, akey) = extractDatSignerParts(tdat)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Resource Verification Error',
                                'Missing or Invalid signer field. {}'.format(ex))


        try:   # Get validated holder agent resource from database
            adat, aser, asig = dbing.getSigned(adid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                    'Error verifying signer resource. {}'.format(ex))

        # Get validated server resource from database
        sdid = keeping.gKeeper.did
        try:
            sdat, sser, ssig = dbing.getSigned(sdid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Resource Verification Error',
                                    'Error verifying signer resource. {}'.format(ex))

        ser = serb.decode("utf-8")
        try:
            dat = validateSignedOfferData(adat, ser, sig, tdat)
        except ValidationError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Validation Error',
                                    'Invalid offer data. {}'.format(ex))


        dt = datetime.datetime.now(tz=datetime.timezone.utc)
        # build signed offer
        odat, oser, osig = buildSignedServerOffer(dat, ser, sig, tdat, sdat, dt,
                                                  sk=keeping.gKeeper.sigkey)

        # validate that no unexpired offers
        entries = dbing.getOfferExpires(did)
        if entries:
            entry = entries[-1]
            edt = arrow.get(entry["expire"])
            if dt <= edt:  # not yet expired
                raise falcon.HTTPError(falcon.HTTP_400,
                                               'Validation Error',
                                            'Unexpired prevailing offer.')


        # Build database key for offer
        key = "{}/offer/{}".format(did, odat["uid"])

        # save offer to database, raise error if duplicate
        try:
            dbing.putSigned(key=key, ser=oser, sig=osig, clobber=False)  # no clobber so error
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))


        # save entry to offer expires database
        odt = arrow.get(odat["expiration"])
        result = dbing.putDidOfferExpire(did=did,
                                         ouid=odat["uid"],
                                         expire=odat["expiration"])
        if not result:  # should never happen
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Database Table Error',
                                               'Failure making entry.')


        didUri = falcon.uri.encode_value(did)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}/{}/offer?uid={}".format(THING_BASE_PATH,
                                                          didUri,
                                                          odat["uid"])
        rep.body = json.dumps(odat, indent=2)

    def on_get(self, req, rep, did):
        """
        Handles GET request for Thing offer resource with did
        and uid in query params
        """
        ouid = req.get_param("uid") # returns url-decoded query parameter value

        key = "{}/offer/{}".format(did, ouid)

        # read from database
        try:
            dat, ser, sig = dbing.getSigned(key)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser

class ThingDidAcceptResource:
    """
    Thing Did Accept Resource
    Accept roffer to transfer title to Thing at DID message

    /thing/{did}/accept?uid=ouid

    did is thing did

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

    The value of the did to offer expires entry
    {
        "offer": "{did}/offer/{ouid}",  # key of offer entry in core database
        "expire": "2000-01-01T00:36:00+00:00", #  ISO-8601 expiration date of offer
    }


    Database key is
    did/offer/ouid


    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    def on_post(self, req, rep, did):
        """
        Handles POST requests

        Post body is new Thing resource with new signer
        """
        ouid = req.get_param("uid") # returns url-decoded query parameter value

        try:  # validate did
            tkey = extractDidParts(did)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Resource Verification Error',
                                           'Invalid did. {}'.format(ex))

        key = "{}/offer/{}".format(did, ouid)

        # read offer from database
        try:
            odat, oser, osig = dbing.getSigned(key)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        dt = datetime.datetime.now(tz=datetime.timezone.utc)

        # validate offer has not yet expired
        odt = arrow.get(odat["expiration"])
        if dt > odt:  # expired
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                        'Expired offer.')

        # validate offer is latest
        entries = dbing.getOfferExpires(did)
        if entries:
            entry = entries[-1]
            edt = arrow.get(entry["expire"])
            if odt != edt or entry['offer'] != key:  # not latest offer
                raise falcon.HTTPError(falcon.HTTP_400,
                                               'Validation Error',
                                            'Not latest offer.')


        adid = odat['aspirant']
        try:  # validate validate aspirant did
            akey = extractDidParts(adid)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Resource Verification Error',
                                           'Invalid did field. {}'.format(ex))

        # read aspirant data resource from database
        try:
            adat, aser, asig = dbing.getSelfSigned(adid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))


        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)
        sig = sigs.get('signer')  # str not bytes
        if not sig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                       'Could not read the request body.')
        ser = serb.decode("utf-8")

        try:
            dat = validateSignedThingTransfer(adat=adat, tdid=did, sig=sig, ser=ser)
        except ValidationError as  ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                               'Validation Error',
                        'Error validating the request body. {}'.format(ex))

        # write new thing resource to database
        try:
            dbing.putSigned(key=did, ser=ser, sig=sig, clobber=True)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))



        didUri = falcon.uri.encode_value(did)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}/{}".format(THING_BASE_PATH, didUri)
        rep.body = json.dumps(dat, indent=2)


class AnonMsgResource:
    """
    Anonymous Message Resource
    Create and Read anonymous messages
    /anon
    /anon?uid=abcdef12

    Database key is
    uid

    {
        create: serverdatetimecreatestamp,
        expire: serverdatetimeexpirestamp
        anon:
        {
            uid: uid,
            content: xoredgatewaylocationstringormsg,
            date: gatewaydatetime,
        }
    }

    uid is  message uid string up to 32 bytes
         if tracker then ephemeral ID in base64 url safe
    content is message content string up to 256 bytes
         if tracker then location string in in base64 url safe
    dts is iso8601 datetime stamp

    The value of the entry is serialized JSON
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

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    def on_post(self, req, rep):
        """
        Handles POST requests

        Post body is tracking message from Gateway

        {
            uid: "AQIDBAoLDA0=",  # base64 url safe of 8 byte eid
            content: "EjRWeBI0Vng=", # base64 url safe of 8 byte location
            date: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of anon gateway time
        }

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
        try:
            serb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                       'Could not read the request body.')
        ser = serb.decode("utf-8")

        try:
            dat = validateAnon(ser=ser)
        except ValidationError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                                               'Validation Error',
                            'Error validating the request body. {}'.format(ex))

        uid = dat['uid']
        dt = datetime.datetime.now(tz=datetime.timezone.utc)
        create = int(dt.timestamp() * 1000000)  # timestamp in microseconds since epoch
        expire = create + int(TRACK_EXPIRATION_DELAY * 1000000)
        sdat = ODict()
        sdat["create"] = create
        sdat["expire"] = expire
        sdat["anon"] = dat

        # write new anon data resource to database at uid
        try:
            dbing.putAnonMsg(key=uid, data=sdat)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))


        # write new expiration of anon uid to database
        try:
            dbing.putExpireUid(key=expire, uid=uid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))

        eidUri = falcon.uri.encode_value(uid)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}?uid={}".format(ANON_MSG_BASE_PATH, eidUri)
        rep.body = json.dumps(sdat, indent=2)

    def on_get(self, req, rep):
        """
        Handles GET request for anon resource and uid in query params
        """
        uid = req.get_param("uid") # returns url-decoded query parameter value

        if not uid:
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Resource Error',
                                    'Missing or invalid query parameter uid.')

        # read all tracks from database
        tracks = []
        try:
            tracks = dbing.getAnonMsgs(key=uid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Error',
                            'Resource malformed. {}'.format(ex))

        if not tracks:
            raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                                               'Not Found Error',
                                               'Track does not exist')

        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = json.dumps(tracks, indent=2)

class CheckHidResource:
    """
    Check Hid  Resource

    Responds to challenge for hid namespace
    used as demonstration

    Attributes:
        .store is reference to ioflo data store

    """
    def  __init__(self, store=None, **kwa):
        """
        Parameters:
            store is reference to ioflo data store
        """
        super(**kwa)
        self.store = store

    def on_get(self, req, rep):
        """
        Handles GET request for HID namespace check given by
        query parameters:
        did for issuing agent
        check (challenge) text is concatenation of:
               did|issuer|date
               where issuer is from issuants in agent resource
               date is iso-8601 date

        Response is signature in signature header with json body
        {
            signer: keyedsignerkeyfromagent,
            check: did|issuer|date
        }

        """
        # have to create so test verify HID has keys to respond put in demo db
        agents, things = dbing.setupTestDbAgentsThings(dbn='demo', clobber=True)

        qargs = httping.parseQuery(req.query_string)  # avoid double unquote bug in falcon
        did = qargs.get('did')
        check = qargs.get('check')
        #did = req.get_param("did")  # already has url-decoded query parameter value
        #check = req.get_param("check")  # already has url-decoded query parameter value
        if not did or not check:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           "Query Parameter Error",
                                    "Missing query parameter one of ('did','check')")

        # read from database
        try:
            dat, ser, sig = dbing.getSelfSigned(did, dbn='demo')
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying resource. {}'.format(ex))

        # get verification key
        index = 0
        key = dat['keys'][index]['key']

        # find signing key
        sk = None
        vk = None
        for agent in agents.values():  # find match
            adid, avk, ask = agent
            if adid == did:  # found
                sk = ask
                vk = avk
                break

        if not sk or not vk:
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Resource Verification Error',
                                    'DID not match. {}'.format(ex))

        #seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)
        # ike's seed
        #seed = (b'!\x85\xaa\x8bq\xc3\xf8n\x93]\x8c\xb18w\xb9\xd8\xd7\xc3\xcf\x8a\x1dP\xa9m'
                #b'\x89\xb6h\xfe\x10\x80\xa6S')

        ## creates signing/verification key pair
        #vk, sk = libnacl.crypto_sign_seed_keypair(seed)

        verkey = keyToKey64u(vk)
        if verkey != key:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           "Invalid Key",
                            "Unexpected Key")

        # sign and return
        sig = keyToKey64u(libnacl.crypto_sign(check.encode("utf-8"), sk)[:libnacl.crypto_sign_BYTES])

        signer = "{}#{}".format(did, index)
        data = ODict()
        data['signer'] = signer
        data['check'] = check

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = json.dumps(data, indent=2)


def loadEnds(app, store):
    """
    Load endpoints for app with store reference
    This function provides the endpoint resource instances
    with a reference to the data store
    """
    server = ServerResource(store=store)
    app.add_route('{}'.format(SERVER_BASE_PATH), server)

    agent = AgentResource(store=store)
    app.add_route('{}'.format(AGENT_BASE_PATH), agent)

    agentDid = AgentDidResource(store=store)
    app.add_route('{}/{{did}}'.format(AGENT_BASE_PATH), agentDid)

    agentDrop = AgentDidDropResource(store=store)
    app.add_route('{}/{{did}}/drop'.format(AGENT_BASE_PATH), agentDrop)

    thing = ThingResource(store=store)
    app.add_route('{}'.format(THING_BASE_PATH), thing)

    thingDid = ThingDidResource(store=store)
    app.add_route('{}/{{did}}'.format(THING_BASE_PATH), thingDid)

    thingOffer = ThingDidOfferResource(store=store)
    app.add_route('{}/{{did}}/offer'.format(THING_BASE_PATH), thingOffer)

    thingAccept = ThingDidAcceptResource(store=store)
    app.add_route('{}/{{did}}/accept'.format(THING_BASE_PATH), thingAccept)

    anon = AnonMsgResource(store=store)
    app.add_route('{}'.format(ANON_MSG_BASE_PATH), anon)

    checkHid = CheckHidResource(store=store)
    app.add_route('{}/check'.format(DEMO_BASE_PATH), checkHid)
