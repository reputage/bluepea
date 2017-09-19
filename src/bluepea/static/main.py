"""
All Browser Javascript globals are available as if imported

Such as
from ... import document
from ... import window

Assumes that the mithril.js script has already been loaded
so m is available as if
from mithril.js import m
"""
import pylib.hello

root = document.body

# note class "ui button" is semantic-ui class

m.render(root, [m("h1", {"class": "title"}, "Hello Python World"),
                m("button", {"class": "ui button"}, "Go Python"),
               ])



#pylib.hello.test()  # shows that python import works
