import json
from hashlib import md5
import logging

import re
from urlparse import urlparse, urlunparse

import requests



STATUS_1xx = re.compile('^1\d\d$')
log = logging.getLogger('blink.client')


class Pool(object):
    pass


class Request(object):

    def __init__(self, server, cache):
        self.server = server
        self.cache = cache
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
        self.id = md5(url).hexdigest()

    def GET(self, url):
        lookup = self.cache.get_etag(self)
        if lookup:
            log.info('[Request] returning cached value based on etag')
            return lookup
        return requests.get(self.merge(url))


_cache = {
    'etags_to_replies': {},
    'request_to_etag': {}
}

class Cache(object):

    def add_etag(self, etag, request, response):
        _cache['etags_to_replies'][etag] = response
        _cache['request_to_etag'][request.id] = etag
        log.info('[Cache] caching response based on etag')

    def get_etag(self, request):
        log.info('[Cache] looking for cached response: {0}'.format(request.id))
        etag = _cache['request_to_etag'].get(request.id)
        if not etag:
            return

        log.info('[Cache] found cached response based on etag')
        return _cache['etags_to_replies'].get(etag)


class JSONParser(object):

    def __call__(self, reply):
        return json.loads(reply.content)


class NullParser(object):

    def __call__(self, reply):
        pass


parser_registry = {'application/json': JSONParser()}

class Response(object):

    def __init__(self, request, cache):
        self.request = request
        self.cache = cache

    def __call__(self, reply):
        self.reply = reply
        self.data = None
        self.parser = self.find_parser()
        self.find_status()
        self.find_cache_headers()

    def find_cache_headers(self):
        print self.reply.headers
        etag = self.reply.headers.get('etag', '')
        if not etag:
            log.info('[Response] no etag to cache on')
            return

        self.cache.add_etag(etag, self.request, self.reply)

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
        print self.reply.headers['Content-Length']
        content_type = self.reply.headers['Content-Type']
        parser = parser_registry.get(content_type, NullParser())
        log.info('[Response] parser found {0}'.format(parser.__class__.__name__))
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


class Wrapper(object):

    def __init__(self, request, response, attr):
        self.attr = attr
        self.request = request
        self.response = response

    def __call__(self, url):
        self.response(self.request(self.attr, url))
        return self.response


class API(object):

    def __init__(self, server, pool=None, request=None, response=None, cache=None):
        self.server = urlparse(server)
        self.pool = pool or Pool()
        self.cache = cache or Cache()
        self.request = request or Request(self.server, self.cache)
        self.response = response or Response(self.request, self.cache)

    def __getattr__(self, attr):
        if attr in self.request.verbs:
            return Wrapper(self.request, self.response, attr)
        raise AttributeError


if __name__=='__main__':
    api = API('http://localhost:8001')
    print(api.GET('/generic/seller/'))
    print(api.GET('/generic/seller/'))
