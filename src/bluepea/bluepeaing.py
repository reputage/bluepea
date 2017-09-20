# -*- coding: utf-8 -*-
"""
Generic Constants and Classes
"""
from __future__ import generator_stop

import sys

SEPARATOR =  "\r\n\r\n"
SEPARATOR_BYTES = SEPARATOR.encode("utf-8")
DID_LENGTH = 52

PROPAGATION_DELAY = 60.0  # network propagation time for consensus

#TRACK_EXPIRATION_DELAY = 60 * 60 * 24  # 24 hours in units of seconds
TRACK_EXPIRATION_DELAY =  10

fakeHidKind = False  # module global flag, If True enable fake hid kind that does not require validation

class BluepeaError(Exception):
    """
    Base Class for bluepea exceptions

    To use   raise BluepeaError("Error: message")
    """

class ValidationError(BluepeaError):
    """
    Validation related errors
    Usage:
        raise ValidationError("error message")
    """
