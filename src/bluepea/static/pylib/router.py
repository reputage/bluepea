"""
Routing between urls and pages.
"""
from .pylib import inspector


def route(root):
    m.route(root, "/inspector",
        {
            "/inspector": inspector.Renderer
        })
