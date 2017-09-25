"""
All Browser Javascript globals are available as if imported

Such as
from ... import document
from ... import window

Assumes that the mithril.js script has already been loaded
so m is available as if
from mithril.js import m
"""
from pylib import router

router.route(document.body)
