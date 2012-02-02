Configuring Django
==================

Setup
-----

Using the Django integration is as simple as adding Raven to your installed apps::

    INSTALLED_APPS = (
        'raven.contrib.django',
    )

Additional settings for the client are configured using ``SENTRY_<setting name>``::

    SENTRY_KEY = 'my secret key'
    SENTRY_SERVERS = ['http://sentry.local/api/store/']

You'll be referencing the client slightly differently in Django as well::

    from raven.contrib.django.models import get_client

    client = get_client()
    client.capture(....)

Integration with ``logging``
----------------------------

Django 1.3
~~~~~~~~~~

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
                'class': 'raven.contrib.django.handlers.SentryHandler',
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


Older Versions
~~~~~~~~~~~~~~

::

    from raven.conf import setup_logging
    from raven.contrib.django.handlers import SentryHandler

    setup_logging(SentryHandler())

Usage
~~~~~

Logging usage works the same way as it does outside of Django, with the addition of an optional ``request`` key in the extra data::

    logger.error('There was some crazy error', exc_info=True, extra={
        # Optionally pass a request and we'll grab any information we can
        'request': request,
    })


404 Logging
-----------

In certain conditions you may wish to log 404 events to the Sentry server. To do this, you simply need to enable a Django middleware::

    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
      ...,
      'raven.contrib.django.middleware.Sentry404CatchMiddleware',
    )

Message References
------------------

Sentry supports sending a message ID to your clients so that they can be tracked easily by your development team. There are two ways to access this information, the first is via the ``X-Sentry-ID`` HTTP response header. Adding this is as simple as appending a middleware to your stack::

    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
      # We recommend putting this as high in the chain as possible
      'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
      ...,
    )

Another alternative method is rendering it within a template. By default, Sentry will attach request.sentry when it catches a Django exception. In our example, we will use this information to modify the default 500.html which is rendered, and show the user a case reference ID. The first step in doing this is creating a custom ``handler500`` in your ``urls.py`` file::

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

Once we've successfully added the request context variable, adding the Sentry reference ID to our 500.html is simple::

    <p>You've encountered an error, oh noes!</p>
    {% if request.sentry.id %}
        <p>If you need assistance, you may reference this error as <strong>{{ request.sentry.id }}</strong>.</p>
    {% endif %}

WSGI Middleware
---------------

If you are using a WSGi interface to serve your app, you can also apply a middleware which will ensure that you
catch errors even at the fundamental level of your Django application::

    from raven.contrib.django.middleware.wsgi import Sentry
    application = Sentry(django.core.handlers.wsgi.WSGIHandler())

Additional Settings
-------------------

SENTRY_CLIENT
~~~~~~~~~~~~~~

In some situations you may wish for a slightly different behavior to how Sentry communicates with your server. For
this, Raven allows you to specify a custom client::

    SENTRY_CLIENT = 'raven.contrib.django.DjangoClient'

Caveats
-------

Error Handling Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have middleware in place that handles ``process_exception`` you will need to take extra care when using Sentry.

For example, the following middleware would suppress Sentry logging due to it returning a response::

    class MyMiddleware(object):
        def process_exception(self, request, exception):
            return HttpResponse('foo')

To work around this, you can either disable your error handling middleware, or add something like the following::

    from django.core.signals import got_request_exception
    class MyMiddleware(object):
        def process_exception(self, request, exception):
            # Make sure the exception signal is fired for Sentry
            got_request_exception.send(sender=self, request=request)
            return HttpResponse('foo')

Or, alternatively, you can just enable Sentry responses::

    from raven.contrib.django.models import sentry_exception_handler
    class MyMiddleware(object):
        def process_exception(self, request, exception):
            # Make sure the exception signal is fired for Sentry
            sentry_exception_handler(request=request)
            return HttpResponse('foo')
