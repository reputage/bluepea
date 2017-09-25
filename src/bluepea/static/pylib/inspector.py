"""
Inspector page, used for viewing objects in the database.
"""


class Tab:
    """
    Base class of tabs, including the menu link and the displayed tab itself.
    """
    Name = ""
    """Friendly name to be displayed in the menu."""
    Data_tab = ""
    """Tab identifier, used as html attribute 'data-tab'."""
    Active = False
    """True if this Tab should be displayed on startup."""

    def __init__(self):
        self._menu_attrs = {"data-tab": self.Data_tab}
        self._tab_attrs = {"data-tab": self.Data_tab}
        self._menu = "a.item"
        self._tab = "div.ui.bottom.attached.tab.segment"

        if self.Active:
            self._menu += ".active"
            self._tab += ".active"

    def menu_item(self):
        """
        Returns a vnode <a> item, for use in the tab menu.
        """
        return m(self._menu, self._menu_attrs, self.Name)

    def tab_item(self):
        """
        Returns a vnode tab wrapper around the contents of the tab itself.
        """
        return m(self._tab, self._tab_attrs, self.main_view())

    def main_view(self):
        """
        Returns the vnode of the actual tab contents.
        """
        return m("div", "hello " + self.Name)


class Entities(Tab):
    Name = "Entities"
    Data_tab = "entities"
    Active = True

    _view = {
        "view": lambda: m("div", "hello Entities")
    }

    def main_view(self):
        return m(self._view)


class Issuants(Tab):
    Name = "Issuants"
    Data_tab = "issuants"


class Offers(Tab):
    Name = "Offers"
    Data_tab = "offers"


class Messages(Tab):
    Name = "Messages"
    Data_tab = "messages"


class AnonMsgs(Tab):
    Name = "Anon Msgs"
    Data_tab = "anonmsgs"


class Tabs:
    """
    Manages the displayed tabs.
    """
    def __init__(self):
        self.tabs = [Entities(), Issuants(), Offers(), Messages(), AnonMsgs()]

        # Required to activate tab functionality (so clicking a menu item will activate that tab)
        jQuery(document).ready(lambda: jQuery('.menu .item').tab())

    def view(self):
        menu_items = []
        tab_items = []
        for tab in self.tabs:
            menu_items.append(tab.menu_item())
            tab_items.append(tab.tab_item())

        return m("div",
                 m("div.ui.top.attached.pointing.menu",
                   menu_items
                   ),
                 tab_items
                 )


tabs = Tabs()
Renderer = {
    "render": tabs.view
}
