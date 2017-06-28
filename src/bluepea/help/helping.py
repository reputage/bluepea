# -*- encoding: utf-8 -*-
"""
Helping Module

"""
from __future__ import generator_stop

import os
import stat
from collections import OrderedDict as ODict, deque
import enum

try:
    import simplejson as json
except ImportError:
    import json

try:
    import msgpack
except ImportError:
    pass

from ioflo.aid.sixing import *
from ioflo.aid import getConsole
from ioflo.aid import filing

console = getConsole()


def dumpKeys(data, filepath):
    '''
    Write data as as type self.ext to filepath. json or msgpack
    '''
    if ' ' in filepath:
        raise IOError("Invalid filepath '{0}' "
                                "contains space".format(filepath))

    perm_other = stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
    perm_group = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
    cumask = os.umask(perm_other | perm_group)  # save old into cumask and set new

    root, ext = os.path.splitext(filepath)
    if ext == '.json':
        with filing.ocfn(filepath, "w+") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.msgpack':
        if not msgpack:
            raise IOError("Invalid filepath ext '{0}' "
                        "needs msgpack installed".format(filepath))
        with filing.ocfn(filepath, "w+b", binary=True) as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError("Invalid filepath ext '{0}' "
                    "not '.json' or '.msgpack'".format(filepath))

    os.umask(cumask)  # restore old


def loadKeys(filepath):
    '''
    Return data read from filepath as converted json
    Otherwise return None
    '''
    try:
        root, ext = os.path.splitext(filepath)
        if ext == '.json':
            with filing.ocfn(filepath, "r") as f:
                it = json.load(f, object_pairs_hook=ODict)
        elif ext == '.msgpack':
            if not msgpack:
                raise IOError("Invalid filepath ext '{0}' "
                            "needs msgpack installed".format(filepath))
            with filing.ocfn(filepath, "rb", binary=True) as f:
                it = msgpack.load(f, object_pairs_hook=ODict)
        else:
            it = None
    except EOFError:
        return None
    except ValueError:
        return None
    return it
