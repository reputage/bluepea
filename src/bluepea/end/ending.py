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

import falcon

from ioflo.aid.sixing import *
from ioflo.aid import getConsole

from ..help.helping import (SEPARATOR, parseSignatureHeader, verify64u,
                            validateSignedAgentReg, validateSignedThingReg,
                            validateSignedResource)
from ..db import dbing

console = getConsole()

AGENT_BASE_PATH = "/agent"
THING_BASE_PATH = "/thing"

class AgentRegister:
    """
    Agent Register Resource

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
        signer = sigs.get('signer')  # str not bytes
        if not signer:
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

        result = validateSignedAgentReg(signer, registration)
        if not result:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                            'Could not validate the request body.')

        if "hids" in result:
            # validate hid control here
            pass


        did = result['did']  # unicode version
        didb = did.encode("utf-8")  # bytes version

        # save to database
        dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
        dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
        with dbing.dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
            rsrcb = txn.get(didb)
            if rsrcb is not None:  # must not be pre-existing
                raise falcon.HTTPError(falcon.HTTP_412,
                                       'Preexistence Error',
                                       'DID already exists')
            resource = registration + SEPARATOR + signer
            txn.put(didb, resource.encode("utf-8") )  # keys and values are bytes

        didURI = falcon.uri.encode_value(did)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}/register?did={}".format(AGENT_BASE_PATH, didURI)
        rep.body = json.dumps(result)

    def on_get(self, req, rep):
        """
        Handles GET request for an AgentResources given by query parameter
        with did


        """
        did = req.get_param("did")  # already has url-decoded query parameter value
        didb = did.encode("utf-8")  # bytes version

        # read fromdatabase
        dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
        dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
        with dbing.dbEnv.begin(db=dbCore) as txn:  # txn is a Transaction object
            rsrcb = txn.get(didb)
            if rsrcb is None:  # does not exist
                raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                                       'Not Found Error',
                                       'DID resource does not exist')

        # should verify that signed at rest is valid by verifying signature
        # of retrieved resource so do not return if resource was corrupted

        resource = rsrcb.decode("utf-8")
        registration, sep, signature = resource.partition(SEPARATOR)
        #reg = json.loads(registration, object_pairs_hook=ODict)

        rep.set_header("Signature", 'signer="{}"'.format(signature))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = registration


class ThingRegister:
    """
    Thing Register Resource

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

        dsig = sigs.get('did')  # str not bytes
        if not dsig:
            raise falcon.HTTPError(falcon.HTTP_400,
                                           'Validation Error',
                                           'Invalid or missing Signature header.')

        ssig = sigs.get('signer')  # str not bytes
        if not ssig:
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

        sdidb = sdid.encode("utf-8")  # bytes version

        # read signer agent from database
        dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
        dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
        with dbing.dbEnv.begin(db=dbCore) as txn:  # txn is a Transaction object
            rsrcb = txn.get(sdidb)
            if rsrcb is None:  # does not exist
                raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                                       'Not Found Error',
                                       'DID resource does not exist')

        resource = rsrcb.decode("utf-8")
        agent, sep, asig = resource.partition(SEPARATOR)
        try:
            agentRsrc = json.loads(agent, object_pairs_hook=ODict)
        except ValueError as ex:
            raise falcon.HTTPError(falcon.HTTP_424,
                                       'Data Resource Error',
                                       'Could not decode associated data resource')

        # Verify that signer agent resource is valid here by looking at agents's
        # signer field and verifying its signature. Signed at rest.

        # Look up signer agent data resource in database
        try:
            adid, aindex = agentRsrc["signer"].rsplit("#", maxsplit=1)
            aindex = int(aindex)  # get index and sdid from signer field
        except (AttributeError, ValueError) as ex:
                raise falcon.HTTPError(falcon.HTTP_400,
                                   'Validation Error',
                                    'Invalid or missing did key index.')   # missing sdid or index

        if adid != agentRsrc['did']:
            raise falcon.HTTPError(falcon.HTTP_424,
                                   'Data Resource Error',
                                   'Signing did mismatch')

        try:
            akey = agentRsrc['keys'][aindex]['key']
        except (IndexError, KeyError) as ex:
            raise falcon.HTTPError(falcon.HTTP_424,
                                           'Data Resource Error',
                                           'Missing signing key')

        if not verify64u(asig, agent, akey):
            raise falcon.HTTPError(falcon.HTTP_424,
                                           'Data Resource Error',
                                           'Invalid signing key')

        # now use signer agents key indexed for thing signer to verify thing resource
        try:
            sverkey = agentRsrc['keys'][index]['key']
        except (IndexError, KeyError) as ex:
            raise falcon.HTTPError(falcon.HTTP_424,
                                           'Data Resource Error',
                                           'Missing signing key')

        if not validateSignedResource(ssig, registration, sverkey):
                raise falcon.HTTPError(falcon.HTTP_400,
                                   'Validation Error',
                                    'Could not validate the request body.')

        if "hid" in result and result["hid"]:  # non-empty hid
            # validate hid control here
            pass

        tdid = result['did']  # unicode version
        tdidb = tdid.encode("utf-8")  # bytes version

        # save to database core
        dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
        dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
        with dbing.dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
            rsrcb = txn.get(tdidb)
            if rsrcb is not None:  # must not be pre-existing
                raise falcon.HTTPError(falcon.HTTP_412,
                                       'Preexistence Error',
                                       'DID already exists')
            resource = registration + SEPARATOR + ssig
            txn.put(tdidb, resource.encode("utf-8") )  # keys and values are bytes

        if result['hid']:  # add entry to hids table to lookup did by hid
            dbHid2Did = dbEnv.open_db(b'hid2did')  # open named sub db named 'hid2did' within env
            with dbing.dbEnv.begin(db=dbHid2Did, write=True) as txn:  # txn is a Transaction object
                txn.put(result['hid'].encode("utf-8"), tdidb)  # keys and values are bytes

        didURI = falcon.uri.encode_value(tdid)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}/register?did={}".format(THING_BASE_PATH, didURI)
        rep.body = json.dumps(result)

    def on_get(self, req, rep):
        """
        Handles GET request for an ThingResources given by query parameter
        with did

        """
        did = req.get_param("did")  # already has url-decoded query parameter value
        didb = did.encode("utf-8")  # bytes version

        # read fromdatabase
        dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
        dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env
        with dbing.dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
            rsrcb = txn.get(didb)
            if rsrcb is None:  # does not exist
                raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                                       'Not Found Error',
                                       'DID resource does not exist')

        # should verify that signed at rest is valid by verifying signature
        # of retrieved resource so do not return if resource was corrupted

        resource = rsrcb.decode("utf-8")
        registration, sep, signature = resource.partition(SEPARATOR)
        #reg = json.loads(registration, object_pairs_hook=ODict)

        rep.set_header("Signature", 'signer="{}"'.format(signature))
        rep.set_header("Content-Type", "application/json; charset=UTF-8")
        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = registration


def loadEnds(app, store):
    """
    Load endpoints for app with store reference
    This function provides the endpoint resource instances
    with a reference to the data store
    """
    agentRegister = AgentRegister(store=store)
    app.add_route('{}/register'.format(AGENT_BASE_PATH), agentRegister)

    thingRegister = ThingRegister(store=store)
    app.add_route('{}/register'.format(THING_BASE_PATH), thingRegister)
