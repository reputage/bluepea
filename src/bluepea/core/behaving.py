# -*- coding: utf-8 -*-
"""
Behaviors
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

import arrow

# Import ioflo libs
from ioflo.aid.sixing import *
from ioflo.aid.odicting import odict
from ioflo.base import doify
from ioflo.aid import getConsole

from ..db import dbing
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

@doify('BluepeaTrackExpire', ioinits=odict(test=""))
def bluepeaTrackExpire(self, **kwa):
    """
    Delete Expired/Stale Tracks

    Assumes that the database has already been setup

    Ioinit attributes
        test is Flag if True use test configuration if any

    Parameters:


    Context: recure

    Example:
        do bluepea track expire
    """
    if dbing.gDbEnv:  # database is setup

        dt = datetime.datetime.now(tz=datetime.timezone.utc)
        date = timing.iso8601(dt, aware=True)


        # read entries earlier than current time
        #entries = dbing.getExpireEid(key=expire)


        # remove entries at expire
        #result = dbing.deleteExpireEid(key=expire)



