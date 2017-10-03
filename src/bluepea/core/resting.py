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

import falcon

from .. import bluepeaing
from ..end import ending, exampling
from ..db import dbing
from ..keep import keeping
from ..help import helping
from ..prime import priming

console = getConsole()

"""
Usage pattern

frame server
  do bluepea server open at enter
  do bluepea server service
  do bluepea server close at exit


"""

@doify('BluepeaServerOpen', ioinits=odict(valet="",
                                          port=odict(ival=8080),
                                          dbDirPath="",
                                          keepDirPath="",
                                          test="",
                                          preload="",
                                          fakeHidKind=odict(ival=False),
                                          ))
def bluepeaServerOpen(self, buffer=False, **kwa):
    """
    Setup and open a rest server

    Ioinit attributes
        valet is Valet instance (wsgi server)
        port is server port
        dbDirPath is directory path for database
        keepDirPath is directory path for private key files
        test is Flag if True load test endpoints and test database
        test is Flag if True and if test is True then preload database for testing
        fakeHidKind is Flag IF True then enable "fake" HID kind that does not require validation

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

    bluepeaing.fakeHidKind = self.fakeHidKind.value   # set global flag

    port = int(self.port.value)
    test = True if self.test.value else False  # use to load test environment
    preload = True if self.preload.value else False  # load test db if test and True

    if test:
        priming.setupTest()
        if preload:
            dbing.preloadTestDbs()
    else:
        keepDirPath = self.keepDirPath.value if self.keepDirPath.value else None  # None is default
        keepDirPath = os.path.abspath(os.path.expanduser(keepDirPath))
        dbDirPath = self.dbDirPath.value if self.dbDirPath.value else None  # None is default
        dbDirPath = os.path.abspath(os.path.expanduser(dbDirPath))
        priming.setup(keepDirPath=keepDirPath, dbDirPath=dbDirPath)

    self.dbDirPath.value = dbing.gDbDirPath
    self.keepDirPath.value = keeping.gKeepDirPath

    app = falcon.API()  # falcon.API instances are callable WSGI apps
    ending.loadEnds(app, store=self.store)

    self.valet.value = Valet(port=port,
                             bufsize=131072,
                             wlog=wlog,
                             store=self.store,
                             app=app,
                             timeout=0.5,
                             )

    result = self.valet.value.servant.reopen()
    if not result:
        console.terse("Error opening server '{0}' at '{1}'\n".format(
                            self.valet.name,
                            self.valet.value.servant.ha))
        return


    console.concise("Opened server '{0}' at '{1}'\n".format(
                            self.valet.name,
                            self.valet.value.servant.ha,))

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


@doify('BluepeaServerClose', ioinits=odict(valet="",))
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
        self.valet.value.servant.closeAll()

        console.concise("Closed server '{0}' at '{1}'\n".format(
                            self.valet.name,
                            self.valet.value.servant.eha))





