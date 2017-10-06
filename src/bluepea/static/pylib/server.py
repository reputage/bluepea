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
        self.refreshAgents = onlyOne(self._refreshAgents)
        self.refreshThings = onlyOne(self._refreshThings)
        self.refreshIssuants = self.refreshAgents
        self.refreshOffers = self.refreshThings

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

            def scope():
                return lambda data: self._parseDIDOffers(did, data)
            promises.append(request("/thing/" + str(did) + "/offer", all=True).then(scope()))
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
        promises = []
        for uid in uids:
            promises.append(request("/anon", uid=uid).then(self._parseOne))
        return Promise.all(promises)

    def _parseOne(self, messages):
        for message in messages:
            self.messages.append(message)


manager = Manager()
