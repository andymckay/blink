import json
from hashlib import md5
import logging

import re
from urllib.parse import urlparse, urlunparse

import requests

from blink.cache import DictCache

STATUS_1xx = re.compile('^1\d\d$')
log = logging.getLogger('blink.client')


class JSONParser(object):

    def __call__(self, reply):
        return reply.json()


class NullParser(object):

    def __call__(self, reply):
        pass

parser_registry = {'application/json': JSONParser()}


class Response(object):

    def __init__(self, request):
        self.request = request

    def __call__(self, reply):
        self.reply = reply
        self.data = None
        self.parser = self.find_parser()
        self.find_status()
        self.parsed = False

    def has_status_code(self, *ranges):
        for code in ranges:
            try:
                res = code.match(str(self.reply.status_code))
            except AttributeError:
                res = str(code) == self.reply.status_code
            if res:
                return res

    def get_length(self):
        length = self.reply.headers.get('Content-Length', None)
        if not length:
            return False

        try:
            length = int(length)
        except:
            log.info('[Response] content-length not an int')
            raise

        return length

    def should_parse(self):
        length = self.get_length()

        if not length:
            log.info('[Response] no content-length using NullParser')
            return False

        if self.has_status_code(STATUS_1xx, 204, 304):
            log.info('[Response] status code is {code} using NullParser'
                     .format(code=str(self.reply.status_code)))
            return False

        return True

    def find_parser(self):
        if not self.should_parse():
            return NullParser()

        content_type = self.reply.headers.get('Content-Type')
        parser = parser_registry.get(content_type, NullParser())
        log.info('[Response] parser found {0}'
                 .format(parser.__class__.__name__))
        return parser

    def find_status(self):
        status = str(self.reply.status_code)
        specific = 'status_{0}'.format(status)
        generic = 'status_{0}xx'.format(status[0])
        method = getattr(self, specific, getattr(self, generic, None))
        if method:
            return method()

    def status_200(self):
        self.data = self.parser(self.reply)

    def status_204(self):
        pass

    def status_2xx(self):
        pass


class Request(object):

    def __init__(self, server, cache=None):
        if not (server.scheme and server.netloc):
            raise ValueError('Server must specify a scheme and netloc.')
        self.server = server
        self.id = None
        self.url = ''
        self.kw = {}

    def config(self, method, url):
        self.method = method
        self.url = self.merge(url)
        self.set_id(url)

    def call(self):
        method = getattr(self, self.method)
        log.info('[Request] GET {0}'.format(self.url))
        return method(self.url)

    def merge(self, url):
        """
        Merge two URLs together, where anything in the given url can override
        anything originally set in the server.
        """
        return urlunparse((u or s for u, s in zip(urlparse(url), self.server)))

    @property
    def verbs(self):
        return ['GET', 'PATCH', 'POST', 'PUT', 'DELETE']

    def set_id(self, url):
        self.id = md5(url.encode('punycode')).hexdigest()

    def get(self, url):
        return requests.get(self.merge(url), **self.kw)


class Resource(object):

    def config(self, cache=None, middleware=None):
        self.cache = (cache or DictCache)()
        self.middleware = middleware or []
        if not isinstance(self.middleware, (list, tuple)):
            self.middleware = self.middleware,
        self.request = Request(self.server)
        self.response = Response(self.request)

    def __init__(self, server):
        self.server = urlparse(server)

    def process(self, attr, url):
        self.request.config(attr, url)

        for middleware in self.middleware:
            mw = middleware(cache=self.cache, request=self.request)
            if hasattr(mw, 'pre') and callable(mw.pre):
                mw.pre()

        reply = self.request.call()
        self.response(reply)

        for middleware in self.middleware:
            mw = middleware(cache=self.cache, request=self.request,
                            response=self.response)
            if hasattr(mw, 'pre') and callable(mw.post):
                mw.post()

        return self
