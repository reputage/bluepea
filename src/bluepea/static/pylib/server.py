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
            msg = AnonMessage(message)
            self.messages.append(msg)


class AnonMessage:
    def __init__(self, data):
        self.uid = data.anon.uid
        self.content = data.anon.content
        self.date = data.anon.date
        self.created = data.create
        self.expire = data.expire
