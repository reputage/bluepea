# -*- encoding: utf-8 -*-
"""
Ending Module

ReST endpoints

"""
from __future__ import generator_stop

from collections import OrderedDict as ODict, deque
import enum
import time

try:
    import simplejson as json
except ImportError:
    import json

import falcon

from ioflo.aid.sixing import *
from ioflo.aid.timing import Stamper
from ioflo.aid import getConsole

from  ..help.helping import backendRequest

console = getConsole()

class ExampleResource:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        message = "\nHello World\n\n"
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.body = message


class ExampleUserResource:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep, userId):
        """
        Handles GET requests
        """
        message = "\nHello World from {}\n\n".format(userId)
        result = ODict(user=userId, msg=message)

        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = json.dumps(result)


    def on_post(self, req, rep, userId):
        """
        Handles POST requests
        """
        try:
            raw_json = req.stream.read()
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_748,
                                       'Read Error',
                                       'Could not read the request body.')

        try:
            data = json.loads(raw_json, 'utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_753,
                                       'Malformed JSON',
                                       'Could not decode the request body. The '
                                       'JSON was incorrect.')

        #console.terse("Received JSON Data: \n{}\n".format(data))

        result = ODict(userId=userId, data=data)

        #rep.status = falcon.HTTP_201
        #rep.location = '/example/%s' % (userId)  # location header redirect

        rep.status = falcon.HTTP_200  # This is the default status
        rep.body = json.dumps(result)

# generator
def textGenerator():
    """
    example generator
    """
    yield bytes()
    time.sleep(0.5)
    yield bytes("\n", "ascii")
    for i in range(10):
        yield bytes("Waiting {}\n".format(i), "ascii")
        time.sleep(0.1)

    yield bytes("\r\n", "ascii")

class ExampleAsyncResource:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        message = "\nHello World\n\n"
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.stream = textGenerator()
        #rep.body = message

# generator
def jsonGenerator():
    """
    example generator that yields empty before yielding json and returning
    """
    for i in range(10):
        yield bytes()
        time.sleep(0.1)
    yield bytes(json.dumps(ODict(name="John Smith", country="United States")), "ascii")
    #yield bytes("\r\n", "ascii")

class ExamplePauseResource:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "application/json"
        rep.stream = jsonGenerator()

class ExampleDidResource:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep, did):
        """
        Handles GET requests

        So falcon automatically url decodes path components
        """
        message = "\nHello World {} from path\n{}\n\n".format(did, req.path)
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.body = message

# deletated generator
def delegator():
    """
    example generator that yields empty bytes before returning data
    """
    for i in range(10):
        yield bytes()
        time.sleep(0.1)
    return ODict(name="John Smith", country="United States")

# generator
def backendGenerator(store=None):
    """
    example generator that yields empty before returning json
    """
    #store = Stamper()
    port = 8101
    path = "/example"

    rep = yield from backendRequest(method='GET',
                                    port=port,
                                    path=path,
                                    store=store,
                                    timeout=0.5)

    #response = yield from delegator()

    if rep is None:  # timed out waiting for authorization server
        pass
        #abortify(app, code=503, text="Timed out authorizing {0}.".format(account))

    if rep['status'] != 200:
        pass
        #emsg = response['data'].get('error', "Unknown")
        #abortify(app, code=response['status'], text="Error '{0}' while "
                 #"authorizing account {1}.".format(emsg, account))

    result = ODict(approved=True,
                   body=rep['body'].decode())
    body = json.dumps(result, indent=2)
    bodyb = body.encode()
    yield bodyb  # returning here breaks


class ExampleBackendResource:
    def  __init__(self, store=None, **kwa):
        super(**kwa)
        self.store = store

    def on_get(self, req, rep):
        """
        Handles GET request that makes request to another backend endpoint
        """
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "application/json"
        rep.stream = backendGenerator(store=self.store)


app = falcon.API() # falcon.API instances are callable WSGI apps

example = ExampleResource()  # Resources are represented by long-lived class instances
app.add_route('/example', example) # example handles all requests to '/example' URL path

exampleUser = ExampleUserResource()
app.add_route('/example/{userId}', exampleUser)

exampleAsync = ExampleAsyncResource()
app.add_route('/example/async', exampleAsync)

examplePause = ExamplePauseResource()
app.add_route('/example/pause', examplePause)

exampleDid = ExampleDidResource()
app.add_route('/example/did/{did}', exampleDid)

exampleBackend = ExampleBackendResource()
app.add_route('/example/backend', exampleBackend)

if __name__ == '__main__':
    from wsgiref import simple_server

    httpd = simple_server.make_server('127.0.0.1', 8080, app)
    httpd.serve_forever()  # navigate web client to http://127.0.0.1:8080/example
