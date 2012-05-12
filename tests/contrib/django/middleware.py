class BrokenRequestMiddleware(object):
    def process_request(self, request):
        raise ImportError('request')


class BrokenResponseMiddleware(object):
    def process_response(self, request, response):
        raise ImportError('response')


class BrokenViewMiddleware(object):
    def process_view(self, request, func, args, kwargs):
        raise ImportError('view')


class FilteringMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, IOError):
            exception.skip_sentry = True
