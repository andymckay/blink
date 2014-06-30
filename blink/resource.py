import json
from hashlib import md5
import logging

import re
from urllib.parse import urlparse, urlunparse

import requests

from blink.cache import NullCache

STATUS_1xx = re.compile('^1\d\d$')
log = logging.getLogger('blink.client')


class JSONParser(object):

    def __call__(self, reply):
        return json.loads(reply.content)


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

    def has_status_code(self, *ranges):
        for code in ranges:
            try:
                res = code.match(self.reply.status_code)
            except AttributeError:
                res = str(code) == self.reply.status_code
            if res:
                return res

    def should_parse(self):
        if self.has_status_code(STATUS_1xx, 204, 304):
            return False

        if self.reply.headers.get('Content-Length') == 0:
            return False

        return True

    def find_parser(self):
        length = self.reply.headers.get('Content-Length', None)
        if not length:
            log.info('[Response] no content-length using NullParser')
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
        self.cache = cache or NullCache()
        self.id = None

    def __call__(self, attr, url):
        self.set_id(url)
        method = getattr(self, attr)
        url = self.merge(url)
        log.info('[Request] GET {0}'.format(url))
        return method(url)

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

    def GET(self, url):
        lookup = self.cache.get_etag(self)
        if lookup:
            log.info('[Request] returning cached value based on etag')
            return lookup
        return requests.get(self.merge(url))


class Resource(object):

    def config(self, pre=None, request=None, response=None, post=None):
        self.pre = pre or []
        self.post = post or []
        self.request = request or Request(self.server)
        self.response = response or Response(self.request)

    def __init__(self, server):
        self.server = urlparse(server)

    def process(self, attr, url):
        for middleware in self.pre:
            middleware.pre(request=self.request)

        reply = getattr(self.request, attr)(url)
        response = self.response(reply)

        for middleware in self.post:
            middleware.post(request=self.request, response=response)

        return response
