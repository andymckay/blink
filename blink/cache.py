import logging

log = logging.getLogger('blink.client')

_cache = {
    'etags_to_replies': {},
    'request_to_etag': {}
}


class NullCache(object):

    def add_etag(self, etag, request, response):
        """ """

    def get_cache(self):
        """ """

    def get_response(self, request):
        """ """

    def get_etag(self, request):
        """ """


class DictCache(object):

    def get_cache(self):
        return _cache

    def add_etag(self, etag, request, response):
        _cache['etags_to_replies'][etag] = response
        _cache['request_to_etag'][request.id] = etag
        log.info('[Cache] caching response based on etag')

    def get_response(self, request):
        etag = self.get_etag(request)
        if not etag:
            return

        log.info('[Cache] found cached response based on etag')
        return _cache['etags_to_replies'].get(etag)

    def get_etag(self, request):
        log.info('[Cache] looking for cached etag: {0}'.format(request.id))
        etag = _cache['request_to_etag'].get(request.id)
        if not etag:
            return

        log.info('[Cache] found cached etag')
        return etag
