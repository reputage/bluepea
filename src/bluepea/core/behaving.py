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

import datetime

# Import ioflo libs
from ioflo.aid.sixing import *
from ioflo.aid.odicting import odict
from ioflo.base import doify
from ioflo.aid import  timing
from ioflo.aid import getConsole

from ..db import dbing
from ..help import helping
from ..prime import priming

console = getConsole()



@doify('BluepeaAnonStaleClear', ioinits=odict(test=""))
def bluepeaAnonStaleClear(self, **kwa):
    """
    Delete Expired/Stale Anon Msgs

    Assumes that the database has already been setup

    Ioinit attributes
        test is Flag if True use test configuration if any

    Parameters:


    Context: recur

    Example:
        do bluepea anon stale clear

    """
    if dbing.gDbEnv:  # database is setup

        dt = datetime.datetime.now(tz=datetime.timezone.utc)
        stamp = int(dt.timestamp() * 1000000)
        date = timing.iso8601(dt, aware=True)

        console.verbose("Clearing Stale Anon Msgs at '{}'\n".format(date))
        try:
            result = dbing.clearStaleAnonMsgs(key=stamp)
        except dbing.DatabaseError as ex:
            console.terse("Error clearing stale anon msgs. {}".format(ex))

        if result:
            console.verbose("Cleared Stale Anon Msgs at '{}'\n".format(date))




