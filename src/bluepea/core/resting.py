# -*- coding: utf-8 -*-
"""
Behaviors for Rest API
"""
from __future__ import generator_stop

import sys
import os

# Import Python libs
from collections import deque
try:
    import simplejson as json
except ImportError:
    import json


# Import ioflo libs
from ioflo.aid.sixing import *
from ioflo.aid import odict
from ioflo.aio import WireLog
from ioflo.aio.http import Valet
from ioflo.base import doify
from ioflo.aid import getConsole

from ..end import ending,  exampling


console = getConsole()

"""
Usage pattern

frame server
  do bluepea server open at enter
  do bluepea server service
  do bluepea server close at exit


"""

@doify('BluepeaServerOpen', ioinits=odict(valet="",
                                          port=odict(inode="", ival=8080),
                                          test=""))
def bluepeaServerOpen(self, buffer=False, **kwa):
    """
    Setup and open a rest server

    Ioinit attributes
        valet is Valet instance (wsgi server)
        mock is Flag if True load mock service endpoints
        test if Flag if True load test endpoints

    Parameters:
        buffer is boolean If True then create wire log buffer for Valet

    Context: enter

    Example:
        do bluepea server open at enter
    """
    if buffer:
        wlog = WireLog(buffify=True, same=True)
        result = wlog.reopen()
    else:
        wlog = None

    port = int(self.port.value)

    #app = bottle.apps.new_app() # create new bottle app
    test = True if self.test.value else False
    #ending.loadAll(app, self.store, test=test)

    app = exampling.app

    self.valet.value = Valet(port=port,
                             bufsize=131072,
                             wlog=wlog,
                             store=self.store,
                             app=app,
                             )

    result = self.valet.value.servant.reopen()
    if not result:
        console.terse("Error opening server '{0}' at '{1}'\n".format(
                            self.valet.name,
                            self.valet.value.servant.eha))
        return


    console.concise("Opened server '{0}' at '{1}'\n".format(
                            self.valet.name,
                            self.valet.value.servant.eha,))

@doify('BluepeaServerService',ioinits=odict(valet=""))
def bluepeaServerService(self, **kwa):
    """
    Service server given by valet

    Ioinit attributes:
        valet is a Valet instance

    Context: recur

    Example:
        do bluepea server service
    """
    if self.valet.value:
        self.valet.value.serviceAll()


@doify('BluepeaServerClose', ioinits=odict(valet=""))
def bluepeaServerClose(self, **kwa):
    """
    Close server in valet

    Ioinit attributes:
        valet is a Valet instance

    Context: exit

    Example:
        do bluepea server close at exit
    """
    if self.valet.value:
        self.valet.value.servant.close()

        console.concise("Closed server '{0}' at '{1}'\n".format(
                            self.valet.name,
                            self.valet.value.servant.eha))


