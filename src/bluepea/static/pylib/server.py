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
        self.refreshAgents = onlyOne(self._refreshAgents)
        self.refreshThings = onlyOne(self._refreshThings)
        self.refreshIssuants = self.refreshAgents

    def _refreshAgents(self):
        while len(self.agents):
            self.agents.pop()
        return request("/agent", all=True).then(self._parseAllAgents)

    def _parseAllAgents(self, dids):
        promises = []
        for did in dids:
            promises.append(request("/agent", did=did).then(self._parseOneAgent))
        return Promise.all(promises)

    def _parseOneAgent(self, data):
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
        promises = []
        for did in dids:
            promises.append(request("/thing", did=did).then(self._parseOneThing))
        return Promise.all(promises)

    def _parseOneThing(self, data):
        self.things.append(data)


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
