# -*- coding: utf-8 -*-
"""
Generic Constants and Classes
"""
from __future__ import generator_stop

import sys

SEPARATOR =  "\r\n\r\n"
SEPARATOR_BYTES = SEPARATOR.encode("utf-8")

class BluepeaError(Exception):
    """
    Base Class for bluepea exceptions

    To use   raise BluepeaError("Error: message")
    """
