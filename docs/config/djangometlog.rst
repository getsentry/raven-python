
Configuring Django with Metlog
==============================

Setup
-----

Using the Django+Metlog integration requires setting the SENTRY_CLIENT
and METLOG attributes in your settings.

The METLOG attribute should point to an actual instance of the metlog
client.  SENTRY_CLIENT must point to
`raven.contrib.django.metlog.MetlogDjangoClient`.

The following shows a configuration using the debug output for metlog ::

    METLOG_CONF = {
        'sender': {
            'class': 'metlog.senders.DebugCaptureSender',
        },
    }

    from metlog.config import client_from_dict_config
    METLOG = client_from_dict_config(METLOG_CONF)

    SENTRY_CLIENT = 'raven.contrib.django.metlog.MetlogDjangoClient'

``RAVEN_CONFIG`` is not required for the MetlogDjangoClient.


You'll be referencing the client the same was as the standard DjangoClient.  ::

    from raven.contrib.django.models import client

    client.captureException()


For simplicity, if SENTRY_CLIENT is set to use MetlogDjangoClient, exceptions will
be collected.  Unlike the standard DjangoClient, there is no way to
disable exception collection.

All other integration with Django's middleware and the python standard
library (in the context of running under Django) works the same as the
standard raven.contrib.django.DjangoClient.

Gunicorn
~~~~~~~~

TODO: need to look at this (vng)
