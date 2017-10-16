from .tests.tester import test

from .pylib import inspector, router

o = require("mithril/ospec/ospec")
sinon = require("sinon")

@test
class Searcher:
    class CaseSensitive:
        def beforeEach(self):
            self.searcher = inspector.Searcher()

        def setSearch(self):
            self.searcher.setSearch('"SensITive"')
            o(self.searcher.searchTerm).equals("SensITive")
            o(self.searcher.caseSensitive).equals(True)

        def searchBasic(self):
            self.searcher.setSearch('"Foo"')

            o(self.searcher.search({
                "bar": "foo"
            })).equals(False)
            o(self.searcher.search({
                "foo": "bar"
            })).equals(False)
            o(self.searcher.search({
                "Foo": "bar"
            })).equals(False)
            o(self.searcher.search({
                "Bar": "Foo"
            })).equals(True)

        def searchNested(self):
            self.searcher.setSearch('"Foo"')

            o(self.searcher.search({
                "bar": {
                    "bar": "foo"
                }
            })).equals(False)
            o(self.searcher.search({
                "bar": {
                    "bar": "Foo"
                }
            })).equals(True)

        def searchList(self):
            self.searcher.setSearch('"Foo"')

            o(self.searcher.search({
                "foo": [0, 1, "foo", 3]
            })).equals(False)
            o(self.searcher.search({
                "foo": [0, 1, "Foo", 3]
            })).equals(True)

        def searchListNested(self):
            self.searcher.setSearch('"Foo"')

            o(self.searcher.search({
                "bar": [0, 1, {
                    "bar": "foo"
                }, [3, "foo", 5], 6]
            })).equals(False)
            o(self.searcher.search({
                "bar": [0, 1, {
                    "bar": "foo"
                }, [3, "Foo", 5], 6]
            })).equals(True)
            o(self.searcher.search({
                "bar": [0, 1, {
                    "bar": "Foo"
                }, [3, "foo", 5], 6]
            })).equals(True)

        def searchInnerString(self):
            self.searcher.setSearch('"Foo"')

            o(self.searcher.search({
                "foo": "blah Fblahooblah blah"
            })).equals(False)
            o(self.searcher.search({
                "foo": "blah blahFooblah blah"
            })).equals(True)

    class CaseInsensitive:
        def beforeEach(self):
            self.searcher = inspector.Searcher()

        def setSearch(self):
            self.searcher.setSearch("InSensItive")
            o(self.searcher.searchTerm).equals("insensitive")
            o(self.searcher.caseSensitive).equals(False)

        def searchBasic(self):
            self.searcher.setSearch('Foo')

            o(self.searcher.search({
                "bar": "foo"
            })).equals(True)
            o(self.searcher.search({
                "foo": "bar"
            })).equals(False)
            o(self.searcher.search({
                "Foo": "bar"
            })).equals(False)
            o(self.searcher.search({
                "Bar": "Foo"
            })).equals(True)

        def searchNested(self):
            self.searcher.setSearch('foo')

            o(self.searcher.search({
                "bar": {
                    "bar": "bar"
                }
            })).equals(False)
            o(self.searcher.search({
                "bar": {
                    "bar": "Foo"
                }
            })).equals(True)

        def searchList(self):
            self.searcher.setSearch('foo')

            o(self.searcher.search({
                "foo": [0, 1, "bar", 3]
            })).equals(False)
            o(self.searcher.search({
                "foo": [0, 1, "Foo", 3]
            })).equals(True)

        def searchInnerString(self):
            self.searcher.setSearch('foo')

            o(self.searcher.search({
                "foo": "blah Fblahooblah blah"
            })).equals(False)
            o(self.searcher.search({
                "foo": "blah blahFooblah blah"
            })).equals(True)

        def searchListNested(self):
            self.searcher.setSearch('foo')

            o(self.searcher.search({
                "bar": [0, 1, {
                    "bar": "boo"
                }, [3, "boo", 5], 6]
            })).equals(False)
            o(self.searcher.search({
                "bar": [0, 1, {
                    "bar": "Foo"
                }, [3, "boo", 5], 6]
            })).equals(True)
            o(self.searcher.search({
                "bar": [0, 1, {
                    "bar": "boo"
                }, [3, "Foo", 5], 6]
            })).equals(True)


@test
class TabledTab:
    _data = [
        {
            "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
            "hid": "hid:dns:localhost#02",
            "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
            "changed": "2000-01-01T00:00:00+00:00",
            "issuants": [
                {
                    "kind": "dns",
                    "issuer": "localhost",
                    "registered": "2000-01-01T00:00:00+00:00",
                    "validationURL": "http://localhost:8080/demo/check"
                }
            ],
            "data":
                {
                    "keywords": ["Canon", "EOS Rebel T6", "251440"],
                    "message": "test message",
                },
            "keys": [
                {
                    "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
                    "kind": "EdDSA"
                },
                {
                    "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",
                    "kind": "EdDSA"
                }
            ],
        },
        {
            "did": "other1",
            "data":
                {
                    "message": "test message"
                }
        },
        {
            "did": "other2",
            "data":
                {
                    "message": "another message"
                }
        }]

    def before(self):
        # Need to make sure startup auto-loading doesn't cause an error, but we don't care about actual data
        self._testServer = sinon.createFakeServer()
        self._testServer.respondWith("[]")
        self._testServer.respondImmediately = True
        window.XMLHttpRequest = XMLHttpRequest

    def after(self):
        self._testServer.restore()

    def asyncBeforeEach(self, done):
        r = router.Router()
        r.route()
        self.tabs = r.tabs
        # Things like "current tab" take a moment to appear in the DOM, so wait for them
        setTimeout(done)

    def startup(self):
        self.tabs.search()
        o(self.tabs.searcher.searchTerm).equals("")("Start with no search")

        current = self.tabs.currentTab()
        o(current.Data_tab).equals(self.tabs.tabs[0].Data_tab)
        o(type(current)).equals(inspector.Entities)("First tab is Entities")

    def _setData(self, callback):
        self.tabs.currentTab().table._setData(self._data)
        self._redraw(callback)

    def _redraw(self, callback):
        m.redraw()
        setTimeout(callback, 50)

    def _clickRow(self, row, callback):
        jQuery("[data-tab='entities'].tab.active table > tbody > tr")[row].click()
        self._redraw(callback)

    def _clickId(self, id, callback):
        jQuery("#" + id).click()
        self._redraw(callback)

    def asyncBasicSearch(self, done, timeout):
        timeout(200)

        jQuery("#" + self.tabs._searchId).val("test message")
        self.tabs.search()
        o(self.tabs.searcher.searchTerm).equals("test message")("Search term set properly")

        def f1():
            rows = jQuery("[data-tab='entities'].tab.active table > tbody > tr")
            o(rows.length).equals(2)("Two search results found")

            def f2():
                rows = jQuery("[data-tab='entities'].tab.active table > tbody > tr")
                o(rows.length).equals(1)("Only one entry in table")
                td = rows.find("td")
                o(td.length).equals(1)("Entry only has one piece of data")
                o(td.text()).equals(inspector.Table.no_results_text)
                done()

            jQuery("#" + self.tabs._searchId).val("not in test data")
            self.tabs.search()

            self._redraw(f2)

        self._setData(f1)

    def asyncSelectRows(self, done, timeout):
        timeout(200)

        def f1():
            def f2():
                tab = self.tabs.currentTab()
                expected = tab.table._stringify(self._data[0])
                actual = jQuery("#" + tab._detailsId).text()
                o(actual).equals(expected)("Details of row 0 are shown")
                o(jQuery("#" + tab._copiedId).text()).equals("")("Copy is empty")

                def f3():
                    expected = tab.table._stringify(self._data[1])
                    actual = jQuery("#" + tab._detailsId).text()
                    o(actual).equals(expected)("Details of row 1 are shown")
                    o(jQuery("#" + tab._copiedId).text()).equals("")("Copy is empty")
                    done()

                self._clickRow(1, f3)

            self._clickRow(0, f2)

        self._setData(f1)

    def asyncDetailsCopy(self, done, timeout):
        timeout(400)

        def f1():
            def f2():
                tab = self.tabs.currentTab()

                def f3():
                    expected = tab.table._stringify(self._data[0])
                    o(jQuery("#" + tab._detailsId).text()).equals(expected)("Details of row 0 are shown")
                    o(jQuery("#" + tab._copiedId).text()).equals(expected)("Details are copied")

                    def f4():
                        o(jQuery("#" + tab._detailsId).text()).equals(expected)("Details are still shown")
                        o(jQuery("#" + tab._copiedId).text()).equals("")("Copy is now empty")
                        done()

                    self._clickId(tab._clearButtonId, f4)

                self._clickId(tab._copyButtonId, f3)

            self._clickRow(0, f2)

        self._setData(f1)

    def asyncRowLimit(self, done):
        table = self.tabs.currentTab().table

        def f1():
            rows = jQuery("[data-tab='entities'].tab.active table > tbody > tr")
            o(rows.length).equals(table.max_size + 1)("Row count limited to max size")
            o(rows.last().find("td").text()).equals(table._limitText())("Last row specifies that text is limited")
            done()

        table.max_size = 50
        data = table._makeDummyData(table.max_size * 2)
        table._setData(data)
        self._redraw(f1)