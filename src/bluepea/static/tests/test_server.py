__pragma__ ('alias', 'Global', 'global')

from .tests.tester import test
from .pylib import server

o = require("mithril/ospec/ospec")
sinon = require("sinon")


@test
class Server:
    def beforeEach(self):
        self.testServer = sinon.createFakeServer()
        window.XMLHttpRequest = Global.XMLHttpRequest

    def afterEach(self):
        self.testServer.restore()

    def _respond(self, request, response):
        request.respond(200, {"Content-Type": "application/json"}, JSON.stringify(response))

    def basicRequest(self):
        endpoint = "/foo"

        def verify(request):
            o(request.method).equals("GET")
            o(request.url).equals(endpoint)
            request.respond(200)
        self.testServer.respondWith(verify)

        server.request(endpoint)
        self.testServer.respond()

    def queryRequest(self):
        endpoint = "/foo"
        full_path = "/foo?one=1&two=2"

        def verify(request):
            o(request.method).equals("GET")
            o(request.url).equals(full_path)
            request.respond(200)
        self.testServer.respondWith(verify)

        server.request(endpoint, one=1, two=2)
        self.testServer.respond()

    def asyncAnonMessages(self, done):
        manager = server.Manager()
        o(len(manager.anonMsgs.messages)).equals(0)("No messages at start")

        def all_(request):
            self._respond(request, ["uid1", "uid2"])
        self.testServer.respondWith("/anon?all=true", all_)

        mContent = "EjRWeBI0Vng="
        mDate = "2017-10-03T20:55:45.186082+00:00"
        mCreate = 1507064140186082
        mExpire = 1507150540186082
        def uid1(request):
            self._respond(request, [
                {
                    "create": mCreate,
                    "expire": mExpire,
                    "anon": {
                        "uid": "uid1",
                        "content": mContent,
                        "date": mDate
                    }
                }
            ])
        self.testServer.respondWith("/anon?uid=uid1", uid1)

        def uid2(request):
            self._respond(request, [])
        self.testServer.respondWith("/anon?uid=uid2", uid2)

        def f1():
            o(len(manager.anonMsgs.messages)).equals(1)("Only one actual message found")
            message = manager.anonMsgs.messages[0]
            o(message.uid).equals("uid1")
            o(message.content).equals(mContent)
            o(message.date).equals(mDate)
            o(message.created).equals(mCreate)
            o(message.expire).equals(mExpire)
            done()

        self.testServer.autoRespond = True
        manager.anonMsgs.refresh().then(f1)
