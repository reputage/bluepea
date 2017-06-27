from __future__ import generator_stop

from collections import OrderedDict as ODict

import pytest
from pytest import approx

import falcon
import pytest_falcon # declares client fixture
from bluepea.end.exampling import app as exapp



@pytest.fixture
def app():
    return exapp

def test_get_example(client):  # client is a fixture in pytest_falcon
    """
    PyTest fixtures are registered globally in the pytest package
    So any test function can accept a fixture as a parameter supplied by
    the pytest runner

    pytest_falcon assumes there is a fixture named "app"
    """
    print("Testing Falcon Example Call")
    rep = client.get('/example')
    assert rep.status == falcon.HTTP_OK
    assert rep.body == '\nHello World\n\n'
    print("Done Test")

def test_get_user(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing Falcon Example User Call")
    rep = client.get('/example/2')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(msg='\nHello World from 2\n\n', user='2')

    headers = {"Content-Type": "application/json; charset=utf-8",
               }
    rep = client.post('/example/2', dict(name="John Smith"), headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(data=dict(name='John Smith'), userId='2')
    print("Done Test")

def test_get_async(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing Falcon Example Async Call")
    rep = client.get('/example/async')
    assert rep.status == falcon.HTTP_OK
    assert rep.body == ('\n'
                        'Waiting 0\n'
                        'Waiting 1\n'
                        'Waiting 2\n'
                        'Waiting 3\n'
                        'Waiting 4\n'
                        'Waiting 5\n'
                        'Waiting 6\n'
                        'Waiting 7\n'
                        'Waiting 8\n'
                        'Waiting 9\n'
                        '\r\n')

    print("Done Test")

def test_get_pause(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing Falcon Example Pause Call")
    rep = client.get('/example/pause')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'country': 'United States', 'name': 'John Smith'}

    print("Done Test")
