Install
=======

If you haven't already, start by downloading Raven. The easiest way is with **pip**::

	pip install raven --upgrade

Or with *setuptools*::

	easy_install -U raven

Requirements
------------

If you installed using pip or setuptools you shouldn't need to worry about requirements. Otherwise
you will need to install the following packages in your environment:

 - ``simplejson``

Upgrading from sentry.client
----------------------------

If you're upgrading from the original ``sentry.client`` there are a few things you will need to note:

* SENTRY_SERVER is deprecated in favor of SENTRY_SERVERS (which is a list of URIs).
* ``sentry.client`` should be replaced with ``raven.contrib.django`` in ``INSTALLED_APPS``.
* ``sentry.client.celery`` should be replaced with ``raven.contrib.django.celery`` in ``INSTALLED_APPS``.
* ``sentry.handlers.SentryHandler`` should be replaced with ``raven.contrib.django.handlers.SentryHandler``
  in your logging configuration.
* All Django specific middleware has been moved to ``raven.contrib.django.middleware``.
* The default Django client is now ``raven.contrib.django.DjangoClient``.
* The Django Celery client is now ``raven.contrib.django.celery.CeleryClient``.
