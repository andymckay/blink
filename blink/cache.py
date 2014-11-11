import logging

try:
    import memcache
    HAS_MEMCACHE = True
except ImportError:
    HAS_MEMCACHE = False

log = logging.getLogger('blink.client.cache')

_cache = {
    'etag_to_response': {},
    'request_to_etag': {}
}


class DictCache(object):

    def __init__(self):
        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)


class MemCache(object):

    def __init__(self):
        self.prefix = 'blink.client'
        self.client = memcache.Client(['127.0.0.1:11211'], debug=0)

    def set(self, key, value):
        log.info('[Memcache] setting {0}'.format(key))
        self.client.set('{0}:{1}'.format(self.prefix, key), value)

    def get(self, key):
        log.info('[Memcache] getting {0}'.format(key))
        return self.client.get('{0}:{1}'.format(self.prefix, key))
