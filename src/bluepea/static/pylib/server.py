"""
Handles interactions with the server endpoints.
"""

__pragma__("kwargs")
def request(path, **kwargs):
    """
    Performs a mithril GET request

    Args:
        path (str): endpoint to access
        qargs (dict): if provided uses this as path query arguments

    Returns:
        Promise from m.request
    """
    path += "?"
    for key, value in kwargs.items():
        path += key + "=" + str(value) + "&"
    path = path[:-1]  # Removed unused & or ?
    return m.request(path)
__pragma__("nokwargs")


class Manager:
    def __init__(self):
        self.anonMsgs = AnonMessages()
        self.entities = Entities()

def onlyOne(func):
    """
    Enforces the promise function is only ever called once.
    """
    scope = {"promise": None}

    def wrap():
        if scope.promise != None:
            return scope.promise

        def f(resolve, reject):
            p = func()
            p.then(resolve)
            p.catch(reject)
        scope.promise = __new__(Promise(f))
        return scope.promise
    return wrap


class Entities:
    def __init__(self):
        self.agents = []
        self.things = []
        self.issuants = []
        self.offers = []
        self.messages = []
        self.refreshAgents = onlyOne(self._refreshAgents)
        self.refreshThings = onlyOne(self._refreshThings)
        self.refreshIssuants = self.refreshAgents
        self.refreshOffers = self.refreshThings
        self.refreshMessages = self.refreshAgents

    def _refreshAgents(self):
        while len(self.agents):
            self.agents.pop()
        return request("/agent", all=True).then(self._parseAllAgents)

    def _parseAllAgents(self, dids):
        """
        [
          "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=",
          "did:igo:QBRKvLW1CnVDIgznfet3rpad-wZBL4qGASVpGRsE2uU=",
          "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
          "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=",
          "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY="
        ]
        """
        promises = []
        for did in dids:
            promises.append(request("/agent", did=did).then(self._parseOneAgent))

            def makeScope(did):
                return lambda data: self._parseDIDMessages(did, data)
            promises.append(request("/agent/" + str(did) + "/drop", all=True).then(makeScope(did)))
        return Promise.all(promises)

    def _parseOneAgent(self, data):
        """
        {
          "did": "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=",
          "signer": "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=#0",
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
        """
        if data.issuants and len(data.issuants) > 0:
            for i in data.issuants:
                # Copy issuant info so we can modify it without affecting the parent agent
                issuant = jQuery.extend(True, {}, i)
                issuant.did = data.did
                self.issuants.append(issuant)
        self.agents.append(data)

    def _parseDIDMessages(self, did, data):
        """
        [
          {
            "from": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
            "uid": "m_00035d3d94be0000_15aabb5"
          }
        ]
        """
        promises = []
        for messagestub in data:
            promises.append(request("/agent/" + str(did) + "/drop", **{"from": messagestub["from"], "uid": messagestub.uid}).then(self._parseDIDMessage))
        return Promise.all(promises)

    def _parseDIDMessage(self, data):
        """
        {
          "uid": "m_00035d3d94be0000_15aabb5",
          "kind": "found",
          "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
          "date": "2000-01-04T00:00:00+00:00",
          "to": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
          "from": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
          "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
          "subject": "Lose something?",
          "content": "I am so happy your found it."
        }
        """
        self.messages.append(data)

    def _refreshThings(self):
        while len(self.things):
            self.things.pop()
        return request("/thing", all=True).then(self._parseAllThings)

    def _parseAllThings(self, dids):
        """
        [
          "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM="
        ]
        """
        promises = []
        for did in dids:
            promises.append(request("/thing", did=did).then(self._parseOneThing))

            def makeScope(did):
                return lambda data: self._parseDIDOffers(did, data)
            promises.append(request("/thing/" + str(did) + "/offer", all=True).then(makeScope(did)))
        return Promise.all(promises)

    def _parseOneThing(self, data):
        """
        {
          "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
          "hid": "hid:dns:localhost#02",
          "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
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
        """
        self.things.append(data)

    def _parseDIDOffers(self, did, data):
        """
        [
          {
            "expire": "2000-01-01T00:22:00+00:00",
            "uid": "o_00035d2976e6a000_26ace93"
          },
          {
            "expire": "2017-10-05T06:38:03.169027+00:00",
            "uid": "o_00035d2976e6a001_26ace99"
          }
        ]
        """
        promises = []
        for offerstub in data:
            promises.append(request("/thing/" + str(did) + "/offer", uid=offerstub.uid).then(self._parseDIDOffer))
        return Promise.all(promises)

    def _parseDIDOffer(self, data):
        """
        {
          "uid": "o_00035d2976e6a000_26ace93",
          "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
          "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
          "duration": 120.0,
          "expiration": "2000-01-01T00:22:00+00:00",
          "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
          "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
          "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ..."
        }
        """
        self.offers.append(data)


class AnonMessages:
    def __init__(self):
        self.messages = []
        self.refresh = onlyOne(self._refresh)

    def _refresh(self):
        while len(self.messages):
            self.messages.pop()
        return request("/anon", all=True).then(self._parseAll)

    def _parseAll(self, uids):
        """
        [
          "AQIDBAoLDA0=",
          "BBIDBAoLCCC="
        ]
        """
        promises = []
        for uid in uids:
            promises.append(request("/anon", uid=uid).then(self._parseOne))
        return Promise.all(promises)

    def _parseOne(self, messages):
        """
        [
          {
            "create": 1507303692490959,
            "expire": 1507390092490959,
            "anon": {
              "uid": "BBIDBAoLCCC=",
              "content": "EjRWeBI0Vng=",
              "date": "2017-10-06T15:28:17.490959+00:00"
            }
          }
        ]
        """
        for message in messages:
            self.messages.append(message)


manager = Manager()
