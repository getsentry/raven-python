"""
raven.contrib.flask.utils
~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
import urlparse

from raven.utils.wsgi import get_headers, get_environ
from werkzeug.exceptions import ClientDisconnected
from flask import current_app

logger = logging.getLogger(__name__)


try:
    from flask_login import current_user
except ImportError:
    has_flask_login = False
else:
    has_flask_login = True


def get_user_info(request):
    """
        Requires Flask-Login (https://pypi.python.org/pypi/Flask-Login/) to be installed
        and setup
    """
    if not has_flask_login:
        return

    if not hasattr(current_app, 'login_manager'):
        return

    try:
        is_authenticated = current_user.is_authenticated()
    except AttributeError:
        # HACK: catch the attribute error thrown by flask-login is not attached
        # >   current_user = LocalProxy(lambda: _request_ctx_stack.top.user)
        # E   AttributeError: 'RequestContext' object has no attribute 'user'
        return {}

    if is_authenticated:
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

    data = {
        'sentry.interfaces.Http': {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': formdata,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }
    }
    try:
        user_data = get_user_info(request)
    except Exception as e:
        logger.exception(e)
    else:
        if user_data:
            data['sentry.interfaces.User'] = user_data

    return data
