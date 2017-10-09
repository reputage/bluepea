# So we can assign javascript global variables
__pragma__ ('alias', 'Global', 'global')

# Mock a window/document environment
jsdom = require('jsdom')
Global.window = __new__(jsdom.JSDOM()).window
Global.document = window.document
Global.XMLHttpRequest = window.XMLHttpRequest

# built-in mithril mock: doesn't appear to work with jQuery
# Global.window = require("mithril/test-utils/browserMock.js")()
# Global.document = window.document

# Our imported modules currently expect these to be available globally
Global.jQuery = require("jquery")
Global.m = require("mithril")
require("../../semantic/dist/semantic")

o = require("mithril/ospec/ospec")


def test(Cls):
    """
    Helper decorator for making test writing easier.

    Wrap around a class to treat the class as though o.spec were called on it.
    Treats any public methods as tests to be run through o(name, method).
    Methods or nested classes starting with an upper case are assumed to be nested test groups,
    and have test() called on them automatically.

    Special o methods (e.g. "beforeEach") are translated to the appropriate o call.
    Additionally, note the following:
        Unlike in regular o() notation, using an async method requires prefacing the function
        with "async"
    """
    class Wrapper:
        def __init__(self):
            original = Cls()

            def dospec():
                funcs = []

                __pragma__('jsiter') # So we can iterate over class methods/nested classes
                for key in original:
                    if key.startswith("_"):
                        continue

                    obj = original[key]

                    if key[0].isupper():
                        # Treat as a nested class to be tested
                        test(obj)
                        continue

                    if key.startswith("async"):
                        # Need to explicitly use a function with done/timeout args
                        def makeScope(fun):
                            return lambda done, timeout: fun(done, timeout)
                        obj = makeScope(obj)
                        key = key[len("async"):]

                    if key in ["beforeEach", "BeforeEach"]:
                        o.beforeEach(obj)
                    elif key in ["before", "Before"]:
                        o.before(obj)
                    elif key in ["afterEach", "AfterEach"]:
                        o.afterEach(obj)
                    elif key in ["after", "After"]:
                        o.after(obj)
                    else:
                        # Treat as a test to run
                        funcs.append((key, obj))
                __pragma__('nojsiter')

                # Actually run the found tests
                for name, func in funcs:
                    o(name, func)

            o.spec(Cls.__name__, dospec)
    Wrapper() # Call immediately, so they don't have to
    return Wrapper
