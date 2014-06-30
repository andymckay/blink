class Pool(object):

    def __init__(self, servers):
        self.servers = list(servers)
        # Assume all servers are active to start with.
        self.active = list(servers)
        self.inactive = []
        self.counter = 0

    def pre(self, request=None):
        pass

    def get(self):
        res = self.active[self.counter]
        self.counter += 1
        if self.counter > len(self.active) - 1:
            self.counter = 0
        return res

    def next(self, server):
        try:
            index = self.active.index(server)
            if index > len(self.active):
                index = 0
            return self.active[index]
        except ValueError:
            return self.get()

    def disable(self, server):
        try:
            index = self.active.index(server)
        except ValueError:
            # If this is run on an already disabled server, check
            # that it is disabled before silently returning.
            assert server in self.inactive
            return

        self.inactive.append(self.active[index])
        del self.active[index]

    def enable(self, server):
        try:
            index = self.inactive.index(server)
        except ValueError:
            # If this is run on an already enabled server, check
            # that it is enabled before silently returning.
            assert server in self.active
            return

        self.active.append(self.inactive[index])
        del self.inactive[index]
