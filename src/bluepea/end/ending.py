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

console = getConsole()


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
        try:
            raw = req.stream.read()
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_748,
                                       'Read Error',
                                       'Could not read the request body.')

        try:
            data = json.loads(raw, 'utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_753,
                                       'Malformed JSON',
                                       'Could not decode the request body. The '
                                       'JSON was incorrect.')

        sig = req.get_header("Signature")


        result = ODict(data=data, sig=sig)

        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = json.dumps(result)


def loadEnds(app, store):
    """
    Load endpoints for app with store reference
    This function provides the endpoint resource instances
    with a reference to the data store
    """
    agentRegister = AgentRegister(store=store)
    app.add_route('/agent/register', agentRegister)
