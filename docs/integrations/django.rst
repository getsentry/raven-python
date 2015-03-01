Django
======

Support
-------

While older versions of Django will likely work, officially only version 1.4 and newer are supported.

Setup
-----

Using the Django integration is as simple as adding :mod:`raven.contrib.django.raven_compat` to your installed apps::

    INSTALLED_APPS = (
        'raven.contrib.django.raven_compat',
    )

.. note:: This causes Raven to install a hook in Django that will automatically report uncaught exceptions.

Additional settings for the client are configured using the ``RAVEN_CONFIG`` dictionary::

    import raven
    RAVEN_CONFIG = {
        'dsn': 'http://public:secret@example.com/1',
        'release': raven.fetch_git_sha(os.path.dirname(__file__)),
    }

Once you've configured the client, you can test it using the standard Django
management interface::

    python manage.py raven test

You'll be referencing the client slightly differently in Django as well::

    from raven.contrib.django.raven_compat.models import client

    client.captureException()


Using with Raven.js
-------------------

A Django template tag is provided to render a proper public DSN inside your templates, you must first load ``raven``::

    {% load raven %}

Inside your template, you can now use::

    <script>Raven.config('{% sentry_public_dsn %}').install()</script>

By default, the DSN is generated in a protocol relative fashion, e.g. ``//public@example.com/1``. If you need a specific protocol, you can override::

    {% sentry_public_dsn 'https' %}

See `Raven.js documentation <http://raven-js.readthedocs.org/>`_ for more information.


Integration with :mod:`logging`
-------------------------------

To integrate with the standard library's :mod:`logging` module:

::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'root': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
        },
        'handlers': {
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'django.db.backends': {
                'level': 'ERROR',
                'handlers': ['console'],
                'propagate': False,
            },
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
            'sentry.errors': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }

Usage
~~~~~

Logging usage works the same way as it does outside of Django, with the
addition of an optional ``request`` key in the extra data::

    logger.error('There was some crazy error', exc_info=True, extra={
        # Optionally pass a request and we'll grab any information we can
        'request': request,
    })


404 Logging
-----------

In certain conditions you may wish to log 404 events to the Sentry server. To
do this, you simply need to enable a Django middleware::

    MIDDLEWARE_CLASSES = (
      'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',
      ...,
    ) + MIDDLEWARE_CLASSES
    
It is recommended to put the middleware at the top, so that any only 404s 
that bubbled all the way up get logged. Certain middlewares (e.g. flatpages)
capture 404s and replace the response.

Message References
------------------

Sentry supports sending a message ID to your clients so that they can be
tracked easily by your development team. There are two ways to access this
information, the first is via the ``X-Sentry-ID`` HTTP response header. Adding
this is as simple as appending a middleware to your stack::

    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
      # We recommend putting this as high in the chain as possible
      'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
      ...,
    )

Another alternative method is rendering it within a template. By default,
Sentry will attach :attr:`request.sentry` when it catches a Django exception.
In our example, we will use this information to modify the default
:file:`500.html` which is rendered, and show the user a case reference ID. The
first step in doing this is creating a custom :func:`handler500` in your
:file:`urls.py` file::

    from django.conf.urls.defaults import *

    from django.views.defaults import page_not_found, server_error

    def handler500(request):
        """
        500 error handler which includes ``request`` in the context.

        Templates: `500.html`
        Context: None
        """
        from django.template import Context, loader
        from django.http import HttpResponseServerError

        t = loader.get_template('500.html') # You need to create a 500.html template.
        return HttpResponseServerError(t.render(Context({
            'request': request,
        })))

Once we've successfully added the :data:`request` context variable, adding the
Sentry reference ID to our :file:`500.html` is simple:

.. code-block:: django

    <p>You've encountered an error, oh noes!</p>
    {% if request.sentry.id %}
        <p>If you need assistance, you may reference this error as <strong>{{ request.sentry.id }}</strong>.</p>
    {% endif %}

WSGI Middleware
---------------

If you are using a WSGI interface to serve your app, you can also apply a
middleware which will ensure that you catch errors even at the fundamental
level of your Django application::

    from raven.contrib.django.raven_compat.middleware.wsgi import Sentry
    from django.core.handlers.wsgi import WSGIHandler

    application = Sentry(WSGIHandler())


Additional Settings
-------------------

SENTRY_CLIENT
~~~~~~~~~~~~~~

In some situations you may wish for a slightly different behavior to how Sentry
communicates with your server. For this, Raven allows you to specify a custom
client::

    SENTRY_CLIENT = 'raven.contrib.django.raven_compat.DjangoClient'

SENTRY_CELERY_LOGLEVEL
~~~~~~~~~~~~~~~~~~~~~~

If you are also using Celery, there is a handler being automatically registered
for you that captures the errors from workers. The default logging level for
that handler is ``logging.ERROR`` and can be customized using this setting::

    SENTRY_CELERY_LOGLEVEL = logging.INFO
    RAVEN_CONFIG = {
        'CELERY_LOGLEVEL': logging.INFO
    }

Caveats
-------

Error Handling Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have middleware in place that handles :func:`process_exception`
you will need to take extra care when using Sentry.

For example, the following middleware would suppress Sentry logging due to it
returning a response::

    class MyMiddleware(object):
        def process_exception(self, request, exception):
            return HttpResponse('foo')

To work around this, you can either disable your error handling middleware, or
add something like the following::

    from django.core.signals import got_request_exception
    class MyMiddleware(object):
        def process_exception(self, request, exception):
            # Make sure the exception signal is fired for Sentry
            got_request_exception.send(sender=self, request=request)
            return HttpResponse('foo')

Note that this technique may break unit tests using the Django test client
(:class:`django.test.client.Client`) if a view under test generates a
:exc:`Http404 <django.http.Http404>` or :exc:`PermissionDenied` exception,
because the exceptions won't be translated into the expected 404 or 403
response codes.

Or, alternatively, you can just enable Sentry responses::

    from raven.contrib.django.raven_compat.models import sentry_exception_handler
    class MyMiddleware(object):
        def process_exception(self, request, exception):
            # Make sure the exception signal is fired for Sentry
            sentry_exception_handler(request=request)
            return HttpResponse('foo')


Gunicorn
~~~~~~~~

If you are running Django with `gunicorn <http://gunicorn.org/>`_ and using the
``gunicorn`` executable, instead of the ``run_gunicorn`` management command, you
will need to add a hook to gunicorn to activate Raven::

    def when_ready(server):
        from django.core.management import call_command
        call_command('validate')

Circus
~~~~~~

If you are running Django with `circus <http://circus.rtfd.org/>`_ and
`chaussette <http://chaussette.readthedocs.org/>`_ you will also need
to add a hook to circus to activate Raven::

    def run_raven(*args, **kwargs):
        """Set up raven for django by running a django command.
        It is necessary because chaussette doesn't run a django command.

        """
        from django.conf import settings
        from django.core.management import call_command
        if not settings.configured:
            settings.configure()

        call_command('validate')
        return True

And in your circus configuration::

    [socket:dwebapp]
    host = 127.0.0.1
    port = 8080

    [watcher:dwebworker]
    cmd = chaussette --fd $(circus.sockets.dwebapp) dproject.wsgi.application
    use_sockets = True
    numprocesses = 2
    hooks.after_start = dproject.hooks.run_raven

