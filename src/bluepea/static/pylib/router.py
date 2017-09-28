"""
Routing between urls and pages.
"""
from .pylib import inspector


def route(root):
    """
    Sets up the routes to pages, based around the given root
    (typically document.body)
    """
    tabs = inspector.Tabs()

    m.route(root, "/inspector",
        {
            "/inspector": {
                "render": tabs.view
            }
        })
