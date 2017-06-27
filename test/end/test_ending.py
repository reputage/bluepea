from __future__ import generator_stop

from collections import OrderedDict as ODict
try:
    import simplejson as json
except ImportError:
    import json

from ioflo.base import storing
import falcon

import pytest
from pytest import approx
import pytest_falcon # declares client fixture
"""
    PyTest fixtures are registered globally in the pytest package
    So any test function can accept a fixture as a parameter supplied by
    the pytest runner

    pytest_falcon assumes there is a fixture named 'app'
"""

import bluepea.end.ending as ending


store = storing.Store(stamp=0.0)

exapp = falcon.API()  # falcon.API instances are callable WSGI apps
ending.loadEnds(exapp, store=store)

@pytest.fixture
def app():
    return exapp

def test_get_AgentRegister(client):  # client is a fixture in pytest_falcon
    """
    Test GET agent/register endpoint with did query parameter
    """
    print("Testing GET /agent/register?did=....")

    rep = client.get('/agent/register?did=did%3Aigo%3Aabcdefghijklmnopqrstuvwxyz')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers == {'content-length': '45', 'content-type': 'application/json; charset=UTF-8'}
    assert rep.body == '{"did": "did:igo:abcdefghijklmnopqrstuvwxyz"}'
    assert rep.json == {'did': 'did:igo:abcdefghijklmnopqrstuvwxyz'}

    print("Done Test")

def test_post_AgentRegister(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing POST /agent/register")

    headers = {"Content-Type": "text/html; charset=utf-8",
               "Signature": "ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789", }
    body = json.dumps(dict(did="did:igo:abcdefghijklmnopqrstuvwxyz",
                           signer="did:igo:abcdefghijklmnopqurstuvwxyz#0"))
    rep = client.post('/agent/register', body=body, headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.headers == {'content-length': '153', 'content-type': 'application/json; charset=UTF-8'}
    assert rep.body == ('{"data": {"did": "did:igo:abcdefghijklmnopqrstuvwxyz", "signer": '
                        '"did:igo:abcdefghijklmnopqurstuvwxyz#0"}, "sig": '
                        '"ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789"}')
    assert rep.json == {'data': {'did': 'did:igo:abcdefghijklmnopqrstuvwxyz',
                        'signer': 'did:igo:abcdefghijklmnopqurstuvwxyz#0'},
                        'sig': 'ABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789'}
    print("Done Test")

