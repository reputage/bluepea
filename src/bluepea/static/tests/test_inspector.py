# So we can assign javascript global variables
__pragma__ ('alias', 'Global', 'global')

# Mock a window/document environment
# Global.window = require("mithril/test-utils/browserMock.js")()
# Global.document = window.document

# Our imported modules currently expect jQuery to be available globally
Global.jQuery = require("jquery")

o = require("mithril/ospec/ospec")

from .pylib import inspector


def test(Cls):
    """
    Helper decorator for making test writing easier.

    Wrap around a class to treat the class as though o.spec were called on it.
    Treats any public methods as tests to be run through o(name, method).
    Methods or nested classes starting with an upper case are assumed to be nested test groups,
    and have test() called on them automatically.
    Special o methods (e.g. "beforeEach") are translated to the appropriate o call.
    """
    class Wrapper:
        def __init__(self):
            original = Cls()

            def dospec():
                funcs = []

                __pragma__('jsiter') # So we can iterate over class methods/nested classes
                for key in original:
                    if key == "beforeEach":
                        o.beforeEach(original[key])
                    else:
                        obj = original[key]
                        if key[0].isupper():
                            # Treat as a nested class
                            test(obj)
                        elif not key.startswith("_"):
                            # Treat as a test to run
                            funcs.append((key, obj))
                __pragma__('nojsiter')

                # Actually run the found tests
                for name, func in funcs:
                    o(name, func)

            o.spec(Cls.__name__, dospec)
    Wrapper() # Call immediately, so they don't have to
    return Wrapper


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
