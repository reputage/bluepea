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

from ioflo.aid.sixing import *
from ioflo.aid import getConsole
from ioflo.aid import timing

from ..bluepeaing import SEPARATOR

from ..help.helping import (parseSignatureHeader, verify64u, extractDidParts,
                            extractDatSignerParts, extractDidSignerParts,
                            validateSignedAgentReg, validateSignedThingReg,
                            validateSignedResource, validateSignedAgentWrite,
                            validateSignedThingWrite,
                            validateMessageData, verifySignedMessageWrite,
                            validateSignedOfferData, buildSignedServerOffer)
from ..db import dbing
from ..keep import keeping

console = getConsole()

AGENT_BASE_PATH = "/agent"
SERVER_BASE_PATH = "/server"
THING_BASE_PATH = "/thing"

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

    def on_post(self, req, rep):
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
            regb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                       'Could not read the request body.')

        registration = regb.decode("utf-8")

        result = validateSignedAgentReg(sig, registration)
        if not result:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                            'Could not validate the request body.')

        if "issuants" in result:
            # validate hid control here
            pass

        did = result['did']  # unicode version

        # save to database
        try:
            dbing.putSigned(registration, sig, did, clobber=False)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))

        didURI = falcon.uri.encode_value(did)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}?did={}".format(AGENT_BASE_PATH, didURI)
        rep.body = json.dumps(result, indent=2)

    def on_get(self, req, rep):
        """
        Handles GET request for an AgentResources given by query parameter
        with did


        """
        did = req.get_param("did")  # already has url-decoded query parameter value

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

    def on_put(self, req, rep, did):
        """
        Handles PUT requests

        /agent/{did}

        Falcon url decodes path parameters such as {did}
        """
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

        # Get validated current resource from database
        try:
            rdat, rser, rsig = dbing.getSelfSigned(did)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying signer resource. {}'.format(ex))

        # validate request
        dat = validateSignedAgentWrite(cdat=rdat, csig=csig, sig=sig, ser=ser)
        if not dat:
            raise falcon.HTTPError(falcon.HTTP_400,
                                               'Validation Error',
                                           'Could not validate the request body.')

        if "issuants" in dat:
            pass  # validate hid namespaces here

        # save to database
        try:
            dbing.putSigned(ser, sig, did, clobber=True)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser

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
        mdat = validateMessageData(mser)

        if not mdat:  # message must not be empty
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Validation Error',
                                    'Invalid message data.')

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
        result = verifySignedMessageWrite(sdat=sdat, index=index, sig=msig, ser=mser)
        if not result:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Validation Error',
                                    'Could not validate the request body.')

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
            dbing.putSigned(mser, msig, key, clobber=False)  # no clobber so error
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

    def on_post(self, req, rep):
        """
        Handles POST requests
        """
        signature = req.get_header("Signature")
        sigs = parseSignatureHeader(signature)

        dsig = sigs.get('did')  # str not bytes thing's did signature
        if not dsig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        tsig = sigs.get('signer')  # str not bytes thing's signer signature
        if not tsig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        try:
            regb = req.stream.read()  # bytes
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_400,
                                       'Read Error',
                                       'Could not read the request body.')

        registration = regb.decode("utf-8")

        # validate thing resource and verify did signature
        result = validateSignedThingReg(dsig, registration)
        if not result:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                            'Could not validate the request body.')

        # verify signer signature by looking up signer data resource in database
        try:
            sdid, index = result["signer"].rsplit("#", maxsplit=1)
            index = int(index)  # get index and sdid from signer field
        except (AttributeError, ValueError) as ex:
                raise falcon.HTTPError(falcon.HTTP_400,
                                   'Validation Error',
                                    'Invalid or missing did key index.')   # missing sdid or index

        # read and verify signer agent from database
        try:
            sdat, sser, ssig = dbing.getSelfSigned(sdid)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                            'Resource Verification Error',
                            'Error verifying signer resource. {}'.format(ex))

        # now use signer agents key indexed for thing signer to verify thing resource
        try:
            tkey = sdat['keys'][index]['key']
        except (TypeError, IndexError, KeyError) as ex:
            raise falcon.HTTPError(falcon.HTTP_424,
                                           'Data Resource Error',
                                           'Missing signing key')

        if not validateSignedResource(tsig, registration, tkey):
                raise falcon.HTTPError(falcon.HTTP_400,
                                   'Validation Error',
                                    'Could not validate the request body.')

        if "hid" in result and result["hid"]:  # non-empty hid
            # validate hid control here
            pass

        tdid = result['did']  # unicode version

        # save to database core
        try:
            dbing.putSigned(registration, tsig, tdid, clobber=False)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))

        if result['hid']:  # add entry to hids table to lookup did by hid
            try:
                dbing.putHid(result['hid'], tdid)
            except DatabaseError as ex:
                raise falcon.HTTPError(falcon.HTTP_412,
                                      'Database Error',
                                      '{}'.format(ex.args[0]))

        didURI = falcon.uri.encode_value(tdid)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}?did={}".format(THING_BASE_PATH, didURI)
        rep.body = json.dumps(result, indent=2)

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

    def on_put(self, req, rep, did):
        """
        Handles PUT requests

        /thing/{did}

        Falcon url decodes path parameters such as {did}
        """
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
        dat = validateSignedThingWrite(sdat=sdat, cdat=cdat, csig=csig, sig=sig, ser=ser)
        if not dat:
            raise falcon.HTTPError(falcon.HTTP_400,
                                               'Validation Error',
                                           'Could not validate the request body.')

        if "hid" in dat:  # new or changed hid
            if (dat["hid"] and not "hid" in cdat) or dat["hid"] != cdat["hid"]:
                pass  # validate hid namespace here

        # save to database
        try:
            dbing.putSigned(ser, sig, did, clobber=True)
        except dbing.DatabaseError as ex:
            raise falcon.HTTPError(falcon.HTTP_412,
                                  'Database Error',
                                  '{}'.format(ex.args[0]))

        rep.set_header("Signature", 'signer="{}"'.format(sig))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = ser

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
    Create proffer to transfer title to Thing at DID message

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

    Database key is
    did/offer/expire

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
        dat = validateSignedOfferData(adat, ser, sig, tdat)

        if not dat:  # offer must not be empty
            raise falcon.HTTPError(falcon.HTTP_400,
                                    'Validation Error',
                                    'Invalid offer data.')


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
            dbing.putSigned(oser, osig, key, clobber=False)  # no clobber so error
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
