from unittest import main, TestCase, TestSuite, TextTestRunner

from blink.cache import MemCache
from blink.middleware.etag import ETag
from blink.resource import Request, Resource
import functools


class API(object):

    def __init__(self, server, **kwargs):
        self.resource = Resource(server)
        self.resource.config(**kwargs)

    def __getattr__(self, attr):
        return functools.partial(self.resource.process, attr)


class TestSamples(TestCase):

    def setUp(self):
        self.api = API('http://localhost:8000/')

    def test_basic(self):
        res = self.api.get('/sample-1-basic.json')
        assert res.response.data == {'hello': 'world'}

    def test_not_json(self):
        res = self.api.get('/sample-2-not-json.html')
        assert res.response.data == None

    def test_no_body(self):
        res = self.api.get('/sample-3-no-body.json')
        assert res.response.data == None


class TestEtag(TestCase):

    def setUp(self):
        self.api = API(
            'http://localhost:8000/',
            middleware=[ETag],
        )

    def test_basic(self):
        res = self.api.get('/sample-1-basic.json')
        assert res.response.data == {'hello': 'world'}
        res = self.api.get('/sample-1-basic.json')
        assert res.response.data == {'hello': 'world'}


class TestMemcache(TestCase):

    def setUp(self):
        self.api = API(
            'http://localhost:8000/',
            middleware=[ETag],
            cache=MemCache
        )

    def test_basic(self):
        res = self.api.get('/sample-1-basic.json')
        assert res.response.data == {'hello': 'world'}
        res = self.api.get('/sample-1-basic.json')
        assert res.response.reply.status_code == 304
        assert res.response.data == {'hello': 'world'}





if __name__=='__main__':
    import logging
    import sys

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(ch)

    main()
