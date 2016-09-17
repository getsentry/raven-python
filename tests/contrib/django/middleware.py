try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object


class BrokenRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        raise ImportError('request')


class BrokenResponseMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        raise ImportError('response')


class BrokenViewMiddleware(MiddlewareMixin):
    def process_view(self, request, func, args, kwargs):
        raise ImportError('view')
