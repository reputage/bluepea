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


class TabledTab(Tab):
    """
    Base class for tabs in the Inspector interface, using a table and "details" view.
    """
    def __init__(self):
        super().__init__()
        self.table = None
        self.setup_table()
        self.copiedDetails = ""

    def setup_table(self):
        """
        Called on startup for the purpose of creating the Table object.
        """
        pass

    def _copyDetails(self):
        self.copiedDetails = self.table.detailSelected

    def _clearCopy(self):
        self.copiedDetails = ""

    def main_view(self):
        return m("div",
                 # Table needs to be in a special container to handle scrolling/sticky table header
                 m("div.table-container", m(self.table.view)),
                 m("div.ui.hidden.divider"),
                 m("div.ui.two.cards", {"style": "height: 45%;"},
                   m("div.ui.card",
                     m("div.content.small-header",
                       m("div.header",
                         m("span", "Details"),
                         m("span.ui.mini.right.floated.button", {"onclick": self._copyDetails}, "Copy")
                         )
                       ),
                     m("pre.content.code-block",
                       self.table.detailSelected
                       )
                     ),
                   m("div.ui.card",
                     m("div.content.small-header",
                       m("div.header",
                         m("span", "Copied"),
                         m("span.ui.mini.right.floated.button", {"onclick": self._clearCopy}, "Clear")
                         )
                       ),
                     m("pre.content.code-block",
                       self.copiedDetails
                       )
                     )
                   )
                 )


class Field:
    """
    A field/column of a table.
    """
    Name = None
    """Friendly name to display in table header."""

    def __init__(self, name=None):
        self.name = self.Name
        if name is not None:
            self.name = name

    def format(self, string):
        """
        Formats the string to match the expected view for this field.
        """
        if len(string) > 8:
            string = string[:5] + "..."
        return string

    def view(self, data):
        """
        Returns a vnode <td> suitable for display in a table.
        """
        return m("td", {"title": data}, self.format(data))


class Table:
    """
    A table, its headers, and its data to be displayed.
    """
    def __init__(self, fields):
        self.max_size = 8
        self.fields = fields
        self.data = {}
        self.view = {
            "oninit": self._oninit,
            "view": self._view
        }
        self._selectedRow = None
        self._selectedUid = None
        self.detailSelected = ""

    def _selectRow(self, event, uid):
        """
        Deselects any previously selected row and
        selects the row specified in the event.
        """
        if uid == self._selectedUid:
            return

        self._selectedUid = uid

        if self._selectedRow is not None:
            jQuery(self._selectedRow).removeClass("active")

        self._selectedRow = event.currentTarget
        jQuery(self._selectedRow).addClass("active")

        self.detailSelected = JSON.stringify(self.data[uid], None, 2)

    def _oninit(self):
        """
        Loads any initial data.
        """
        for i in range(20):
            obj = {}
            for field in self.fields:
                obj[field.name] = "test{0} {1}".format(i, field.name)
            self.data[i] = obj

    def _view(self):
        headers = [m("th", field.name) for field in self.fields]

        # Create the rows of the table
        rows = []
        for i, key in enumerate(self.data.keys()):
            if i >= self.max_size:
                rows.append(m("tr", m("td", "Limited to {} results.".format(self.max_size))))
                break

            obj = self.data[key]
            # Format each cell based on the corresponding Field
            row = [field.view(obj[field.name]) for field in self.fields]

            # Needed so we can pass through the key as-is to the lambda, without it changing through the loop
            def makeScope(uid):
                return lambda event: self._selectRow(event, uid)
            rows.append(m("tr", {"onclick": makeScope(key)}, row))

        return m("table", {"class": "ui selectable celled unstackable single line left aligned table"},
                 m("thead",
                   m("tr", {"class": "center aligned"}, headers)
                   ),
                 m("tbody",
                   rows
                   )
                 )


class Entities(TabledTab):
    Name = "Entities"
    Data_tab = "entities"
    Active = True

    def setup_table(self):
        fields = [Field(x) for x in ["DID", "HID", "Signer", "Changed", "Issuants", "Data", "Keys"]]
        self.table = Table(fields)


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
