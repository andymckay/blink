class Pool(object):

    def __init__(self, servers):
        self.servers = servers
        # Assume all servers are active to start with.
        self.active = list(set(servers))
        self.inactive = {}
        self.counter = 0

    def get(self):
        self.active[self.counter]
        self.counter += 1
        if self.counter > len(self.active):
            self.counter = 0

    def next(self, server):
        try:
            index = self.active.index(server)
            if index > len(self.active):
                index = 0
            return self.active[index]
        except IndexError:
            return self.get()

    def mark(self, server, length):
        self.


