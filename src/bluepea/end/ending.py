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

from ..help.helping import SEPARATOR, parseSignatureHeader, validateSignedAgentReg
from ..db import dbing

console = getConsole()

BASE_PATH = "/agent"

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

    def on_get(self, req, rep):
        """
        Handles GET request for an AgentResources given by query parameter
        with did


        """
        did = req.get_param("did")
        result = ODict(did=did)

        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = json.dumps(result)


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


        did = result['did']  # unicode version
        didb = did.encode("utf-8")  # bytes version

        # save to database
        dbEnv = dbing.dbEnv  # lmdb database env assumes already setup
        dbCore = dbEnv.open_db(b'core')  # open named sub db named 'core' within env

        with dbing.dbEnv.begin(db=dbCore, write=True) as txn:  # txn is a Transaction object
            rsrc = txn.get(didb)
            if rsrc is not None:  # must not be pre-existing
                raise falcon.HTTPError(falcon.HTTP_412,
                                       'Preexistence Error',
                                       'DID already exists')
            resource = registration + SEPARATOR + signer
            txn.put(didb, resource.encode("utf-8") )  # keys and values are bytes

        didURI = falcon.uri.encode_value(did)
        rep.status = falcon.HTTP_201  # post response status with location header
        rep.location = "{}/register?did={}".format(BASE_PATH, didURI)
        rep.body = json.dumps(result)


def loadEnds(app, store):
    """
    Load endpoints for app with store reference
    This function provides the endpoint resource instances
    with a reference to the data store
    """
    agentRegister = AgentRegister(store=store)
    app.add_route('/agent/register', agentRegister)


