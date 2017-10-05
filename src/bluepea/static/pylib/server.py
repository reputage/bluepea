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


class Entities:
    def __init__(self):
        self.agents = []
        self.things = []

    def refreshAgents(self):
        while len(self.agents):
            self.agents.pop()
        return request("/agent", all=True).then(self._parseAllAgents)

    def _parseAllAgents(self, dids):
        promises = []
        for did in dids:
            promises.append(request("/agent", did=did).then(self._parseOneAgent))
        return Promise.all(promises)

    def _parseOneAgent(self, data):
        self.agents.append(data)

    def refreshThings(self):
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

    def refresh(self):
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
