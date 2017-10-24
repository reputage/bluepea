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

    def _respondTo(self, endpoint, data):
        self.testServer.respondWith(endpoint, lambda request: self._respond(request, data))

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

        self._respondTo("/anon?all=true", ["uid1", "uid2"])

        messages1 = [
            {
                "create": 1507064140186082,
                "expire": 1507150540186082,
                "anon": {
                    "uid": "uid1",
                    "content": "EjRWeBI0Vng=",
                    "date": "2017-10-03T20:55:45.186082+00:00"
                }
            }
        ]
        messages2 = []
        self._respondTo("/anon?uid=uid1", messages1)
        self._respondTo("/anon?uid=uid2", messages2)

        def f1():
            o(len(manager.anonMsgs.messages)).equals(1)("Only one actual message found")
            o(manager.anonMsgs.messages[0]).deepEquals(messages1[0])
            done()

        self.testServer.autoRespond = True
        manager.anonMsgs.refresh().then(f1)

    def asyncAgents(self, done):
        manager = server.Manager()
        o(len(manager.entities.agents)).equals(0)

        self._respondTo("/agent?all=true", ["did1", "did2"])
        agent1 = {
          "did": "did1",
          "signer": "did1#0",
          "changed": "2000-01-01T00:00:00+00:00",
          "keys": [
            {
              "key": "3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=",
              "kind": "EdDSA"
            }
          ],
          "issuants": [
            {
              "kind": "dns",
              "issuer": "localhost",
              "registered": "2000-01-01T00:00:00+00:00",
              "validationURL": "http://localhost:8101/demo/check"
            }
          ]
        }
        agent2 = {}
        self._respondTo("/agent?did=did1", agent1)
        self._respondTo("/agent?did=did2", agent2)

        # Don't care about these for this test
        self._respondTo("/agent/did1/drop?all=true", [])
        self._respondTo("/agent/did2/drop?all=true", [])

        def f1():
            o(len(manager.entities.agents)).equals(2)
            o(manager.entities.agents[0]).deepEquals(agent1)
            o(manager.entities.agents[1]).deepEquals(agent2)
            done()

        self.testServer.autoRespond = True
        manager.entities.refreshAgents().then(f1)

    def asyncThings(self, done):
        manager = server.Manager()
        o(len(manager.entities.things)).equals(0)

        self._respondTo("/thing?all=true", ["did1", "did2"])
        thing1 = {
          "did": "did1",
          "hid": "hid:dns:localhost#02",
          "signer": "did2#0",
          "changed": "2000-01-01T00:00:00+00:00",
          "data": {
            "keywords": [
              "Canon",
              "EOS Rebel T6",
              "251440"
            ],
            "message": "If found please return."
          }
        }
        thing2 = {}
        self._respondTo("/thing?did=did1", thing1)
        self._respondTo("/thing?did=did2", thing2)

        # Don't care about these for this test
        self._respondTo("/thing/did1/offer?all=true", [])
        self._respondTo("/thing/did2/offer?all=true", [])

        def f1():
            o(len(manager.entities.things)).equals(2)
            o(manager.entities.things[0]).deepEquals(thing1)
            o(manager.entities.things[1]).deepEquals(thing2)
            done()

        self.testServer.autoRespond = True
        manager.entities.refreshThings().then(f1)

    def asyncIssuants(self, done):
        manager = server.Manager()
        o(len(manager.entities.issuants)).equals(0)

        self._respondTo("/agent?all=true", ["did1", "did2"])
        issuants1 = [
            {
              "kind": "dns",
              "issuer": "localhost",
              "registered": "2000-01-01T00:00:00+00:00",
              "validationURL": "http://localhost:8101/demo/check1"
            },
            {
              "kind": "dns",
              "issuer": "localhost",
              "registered": "2000-01-01T00:00:00+00:00",
              "validationURL": "http://localhost:8101/demo/check2"
            }
          ]
        agent1 = {
          "did": "did1",
          "issuants": issuants1
        }
        issuants2 = [
            {
              "kind": "dns",
              "issuer": "localhost",
              "registered": "2000-01-01T00:00:00+00:00",
              "validationURL": "http://localhost:8101/demo/check3"
            }
        ]
        agent2 = {
            "did": "did2",
            "issuants": issuants2
        }
        self._respondTo("/agent?did=did1", agent1)
        self._respondTo("/agent?did=did2", agent2)

        # Don't care about these for this test
        self._respondTo("/agent/did1/drop?all=true", [])
        self._respondTo("/agent/did2/drop?all=true", [])

        def f1():
            o(len(manager.entities.issuants)).equals(3)

            iss0 = jQuery.extend(True, {"did": "did1"}, issuants1[0])
            o(manager.entities.issuants[0]).deepEquals(iss0)
            iss1 = jQuery.extend(True, {"did": "did1"}, issuants1[1])
            o(manager.entities.issuants[1]).deepEquals(iss1)
            iss2 = jQuery.extend(True, {"did": "did2"}, issuants2[0])
            o(manager.entities.issuants[2]).deepEquals(iss2)

            done()

        self.testServer.autoRespond = True
        manager.entities.refreshIssuants().then(f1)

    def asyncOffers(self, done, timeout):
        timeout(300)
        manager = server.Manager()
        o(len(manager.entities.offers)).equals(0)

        self._respondTo("/thing?all=true", ["did1", "did2"])

        self._respondTo("/thing/did1/offer?all=true", [{"uid": "o_1"}, {"uid": "o_2"}])
        self._respondTo("/thing/did2/offer?all=true", [{"uid": "o_3"}])
        offer1 = {
          "uid": "o_1",
          "thing": "did1",
          "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
          "duration": 120.0,
          "expiration": "2000-01-01T00:22:00+00:00",
          "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
          "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
          "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ"
        }
        offer2 = {
          "uid": "o_2",
          "thing": "did1",
          "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
          "duration": 120.0,
          "expiration": "2000-01-01T00:22:00+00:00",
          "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
          "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
          "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ"
        }
        offer3 = {
          "uid": "o_3",
          "thing": "did2",
          "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
          "duration": 120.0,
          "expiration": "2000-01-01T00:22:00+00:00",
          "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
          "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
          "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ"
        }
        self._respondTo("/thing/did1/offer?uid=o_1", offer1)
        self._respondTo("/thing/did1/offer?uid=o_2", offer2)
        self._respondTo("/thing/did2/offer?uid=o_3", offer3)

        # Don't care about these for this test
        self._respondTo("/thing?did=did1", {})
        self._respondTo("/thing?did=did2", {})

        def f1():
            o(len(manager.entities.offers)).equals(3)
            o(manager.entities.offers[0]).deepEquals(offer1)
            o(manager.entities.offers[1]).deepEquals(offer2)
            o(manager.entities.offers[2]).deepEquals(offer3)
            done()

        self.testServer.autoRespond = True
        manager.entities.refreshOffers().then(f1)

    def asyncMessages(self, done, timeout):
        timeout(300)
        manager = server.Manager()
        o(len(manager.entities.messages)).equals(0)

        self._respondTo("/agent?all=true", ["did1", "did2"])
        self._respondTo("/agent/did1/drop?all=true", [{"from": "did2", "uid": "m_1"}, {"from": "did3", "uid": "m_2"}])
        self._respondTo("/agent/did2/drop?all=true", [{"from": "did1", "uid": "m_3"}])
        message1 = {
          "uid": "m_1",
          "kind": "found",
          "signer": "did2#0",
          "date": "2000-01-04T00:00:00+00:00",
          "to": "did1",
          "from": "did2",
          "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
          "subject": "Lose something?",
          "content": "I am so happy your found it."
        }
        message2 = {
          "uid": "m_2",
          "kind": "found",
          "signer": "did3#0",
          "date": "2000-01-04T00:00:00+00:00",
          "to": "did1",
          "from": "did3",
          "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
          "subject": "Lose something?",
          "content": "I am so happy your found it."
        }
        message3 = {
          "uid": "m_3",
          "kind": "found",
          "signer": "did1#0",
          "date": "2000-01-04T00:00:00+00:00",
          "to": "did2",
          "from": "did1",
          "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
          "subject": "Lose something?",
          "content": "I am so happy your found it."
        }
        self._respondTo("/agent/did1/drop?from=did2&uid=m_1", message1)
        self._respondTo("/agent/did1/drop?from=did3&uid=m_2", message2)
        self._respondTo("/agent/did2/drop?from=did1&uid=m_3", message3)

        # Don't care about these for this test
        self._respondTo("/agent?did=did1", {})
        self._respondTo("/agent?did=did2", {})

        def f1():
            o(len(manager.entities.messages)).equals(3)
            o(manager.entities.messages[0]).deepEquals(message1)
            o(manager.entities.messages[1]).deepEquals(message2)
            o(manager.entities.messages[2]).deepEquals(message3)
            done()

        self.testServer.autoRespond = True
        manager.entities.refreshMessages().then(f1)
