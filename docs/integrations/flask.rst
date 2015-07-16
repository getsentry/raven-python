Flask
=====

`Flask <http://flask.pocoo.org/>`_ is a popular Python micro webframework.
Support for Flask is provided by Raven directly but for some dependencies
you need to install raven with the flask feature set.

Installation
------------

If you haven't already, install raven with its explicit Flask dependencies::

    pip install raven[flask]

Setup
-----

The first thing you'll need to do is to initialize Raven under your application::

    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn='___DSN___')

If you don't specify the ``dsn`` value, we will attempt to read it from
your environment under the ``SENTRY_DSN`` key.

Extended Setup
--------------

You can optionally configure logging too::

    import logging
    from raven.contrib.flask import Sentry
    sentry = Sentry(app, logging=True, level=logging.ERROR)

Building applications on the fly? You can use Raven's ``init_app`` hook::

    sentry = Sentry(dsn='http://public_key:secret_key@example.com/1')

    def create_app():
        app = Flask(__name__)
        sentry.init_app(app)
        return app

You can pass parameters in the ``init_app`` hook::

    sentry = Sentry()

    def create_app():
        app = Flask(__name__)
        sentry.init_app(app, dsn='http://public_key:secret_key@example.com/1',
                        logging=True, level=logging.ERROR)
        return app

Settings
--------

Additional settings for the client can be configured using
``SENTRY_<setting name>`` in your application's configuration::

    class MyConfig(object):
        SENTRY_DSN = '___DSN___'
        SENTRY_INCLUDE_PATHS = ['myproject']

If `Flask-Login <https://pypi.python.org/pypi/Flask-Login/>`_ is used by
your application (including `Flask-Security
<https://pypi.python.org/pypi/Flask-Security/>`_), user information will
be captured when an exception or message is captured.  By default, only
the ``id`` (current_user.get_id()), ``is_authenticated``, and
``is_anonymous`` is captured for the user.  If you would like additional
attributes on the ``current_user`` to be captured,  you can configure them
using ``SENTRY_USER_ATTRS``::

    class MyConfig(object):
        SENTRY_USER_ATTRS = ['username', 'first_name', 'last_name', 'email']

``email`` will be captured as ``sentry.interfaces.User.email``, and any
additionl attributes will be available under
``sentry.interfaces.User.data``

You can specify the types of exceptions that should not be reported by
Sentry client in your application by setting the
``RAVEN_IGNORE_EXCEPTIONS`` configuration value on your Flask app
configuration::

    class MyExceptionType(Exception):
        def __init__(self, message):
            super(MyExceptionType, self).__init__(message)

    app = Flask(__name__)
    app.config["RAVEN_IGNORE_EXCEPTIONS"] = [MyExceptionType]

Usage
-----

Once you've configured the Sentry application it will automatically
capture uncaught exceptions within Flask. If you want to send additional
events, a couple of shortcuts are provided on the Sentry Flask middleware
object.

Capture an arbitrary exception by calling ``captureException``::

    try:
        1 / 0
    except ZeroDivisionError:
        sentry.captureException()

Log a generic message with ``captureMessage``::

    sentry.captureMessage('hello, world!')

Getting the last event id
-------------------------

If possible, the last Sentry event ID is stored in the request context
``g.sentry_event_id`` variable.  This allow to present the user an error
ID if have done a custom error 500 page.

.. code-block:: html+jinja

    <h2>Error 500</h2>
    {% if g.sentry_event_id %}
    <p>The error identifier is {{ g.sentry_event_id }}</p>
    {% endif %}

Dealing with proxies
--------------------

When your Flask application is behind a proxy such as nginx, Sentry will
use the remote address from the proxy, rather than from the actual
requesting computer.  By using ``ProxyFix`` from `werkzeug.contrib.fixers
<http://werkzeug.pocoo.org/docs/0.10/contrib/fixers/#werkzeug.contrib.fixers.ProxyFix>`_
the Flask ``.wsgi_app`` can be modified to send the actual ``REMOTE_ADDR``
along to Sentry. ::

    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

This may also require `changes
<http://flask.pocoo.org/docs/0.10/deploying/wsgi-standalone/#proxy-setups>`_
to the proxy configuration to pass the right headers if it isn't doing so
already.
