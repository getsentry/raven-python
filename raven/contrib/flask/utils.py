import urlparse

def get_data_from_request(request):
    urlparts = urlparse.urlsplit(request.url)

    return {
        'sentry.interfaces.Http': {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': request.form or request.args,
            'env': dict(request.headers),
        }
    }
