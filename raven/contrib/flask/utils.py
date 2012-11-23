import urlparse

from raven.utils.wsgi import get_headers, get_environ
from werkzeug.exceptions import ClientDisconnected


def get_data_from_request(request):
    urlparts = urlparse.urlsplit(request.url)

    try:
        formdata = request.form
    except ClientDisconnected:
        formdata = {}

    return {
        'sentry.interfaces.Http': {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': formdata,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }
    }
