import urlparse

from raven.utils.wsgi import get_headers, get_environ
from werkzeug.exceptions import ClientDisconnected
from flask import current_app


def get_user_info(request):
    """
        Requires Flask-Login (https://pypi.python.org/pypi/Flask-Login/) to be installed
        and setup
    """
    try:
        from flask_login import current_user
    except ImportError:
        return None

    if not hasattr(current_app, 'login_manager'):
        return None

    if current_user.is_authenticated():
        user_info = {
            'is_authenticated': True,
            'is_anonymous': current_user.is_anonymous(),
            'id': current_user.get_id(),
        }

        if 'SENTRY_USER_ATTRS' in current_app.config:
            for attr in current_app.config['SENTRY_USER_ATTRS']:
                if hasattr(current_user, attr):
                    user_info[attr] = getattr(current_user, attr)
    else:
        user_info = {
            'is_authenticated': False,
            'is_anonymous': current_user.is_anonymous(),
        }

    return user_info


def get_data_from_request(request):
    urlparts = urlparse.urlsplit(request.url)

    try:
        formdata = request.form
    except ClientDisconnected:
        formdata = {}

    result = {}

    result['sentry.interfaces.User'] = get_user_info(request)

    result['sentry.interfaces.Http'] = {
        'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
        'query_string': urlparts.query,
        'method': request.method,
        'data': formdata,
        'headers': dict(get_headers(request.environ)),
        'env': dict(get_environ(request.environ)),
    }

    return result
