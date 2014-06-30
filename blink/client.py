from resource import Resource
import functools


class API(object):

    def __init__(self, server, **kwargs):
        self.resource = Resource(server)
        self.resource.config(**kwargs)

    def __getattr__(self, attr):
        return functools.partial(self.resource.process, attr)


if __name__ == '__main__':
    api = API('http://localhost:8001')
    print(api.GET('/generic/seller/'))
    print(api.GET('/generic/seller/'))
