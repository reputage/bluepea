"""
Routing between urls and pages.
"""
from .pylib import inspector


class Router:
    def __init__(self):
        self.tabs = inspector.Tabs()

    def route(self, root=None):
        """
        Sets up the routes to pages, based around the given root
        (typically document.body)
        """
        if root is None:
            root = document.body
        m.route(root, "/inspector",
                {
                    "/inspector": {
                        "render": self.tabs.view
                    }
                })
