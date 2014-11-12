# -*- coding: utf8 -*-
import uuid
from unittest import main, TestCase
from unittest.mock import patch
from urllib.parse import urlparse

from blink.cache import DictCache
from blink.resource import Request, Resource
from blink.pool import Pool


class FakeRequest(object):

    def __init__(self):
        self.id = str(uuid.uuid4())


class FakeResponse(object):
    pass


class FakeRequests(TestCase):

    def setUp(self):
        patcher = patch('requests.get')
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)


class TestRequest(FakeRequests):

    def test_server(self):
        for s in ('/', 'http://', 'f.c'):
            with self.assertRaises(ValueError):
                Request(urlparse(s))

    def test_merge(self):
        for a, b, c in (
                ['http://f.c/', '/f', 'http://f.c/f'],
                ['http://f.c/b', '/f', 'http://f.c/f'],
                ['http://f.c/b?f', 'f', 'http://f.c/f?f'],
            ):
            res = Request(urlparse(a)).merge(b)
            assert res == c, res

    def test_id(self):
        for a in ('/f/b', 'Азәрбајҹан'):
            req = Request(urlparse('http://f.c'))
            req.set_id(a)

    def test_get(self):
        req = Request(urlparse('http://f.c'))
        req.get('/b')
        self.mock.assert_called_with('http://f.c/b')


class TestPool(TestCase):

    def setUp(self):
        self.servers = ('http://f.b/', 'http://b.c/', 'https://g.p')
        self.pool = Pool(self.servers)

    def test_next(self):
        assert self.pool.get() == self.servers[0]
        assert self.pool.get() == self.servers[1]
        assert self.pool.get() == self.servers[2]
        assert self.pool.get() == self.servers[0]

    def test_disable(self):
        self.pool.disable('http://b.c/')
        assert len(self.pool.active) == 2
        assert 'http://b.c/' in self.pool.inactive

    def test_disable_missing(self):
        self.pool.disable('http://b.c/')
        self.pool.disable('http://b.c/')
        assert len(self.pool.active) == 2

    def test_disable_messed_up(self):
        with self.assertRaises(AssertionError):
            self.pool.disable('http://x.c/')

    def test_enable(self):
        self.pool.disable('http://b.c/')
        self.pool.enable('http://b.c/')
        assert len(self.pool.active) == 3
        assert 'http://b.c/' in self.pool.active

    def test_enable_missing(self):
        self.pool.enable('http://b.c/')
        assert len(self.pool.active) == 3

    def test_enable_messed_up(self):
        with self.assertRaises(AssertionError):
            self.pool.disable('http://x.c/')


class TestResource(FakeRequests):

    def test(self):
        res = Resource('http://f.com')
        res.config()
        res.process('get', '/b')


if __name__=='__main__':
    main()
