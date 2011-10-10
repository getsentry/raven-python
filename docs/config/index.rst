Configuration
=============

This document describes configuration options available to Sentry.

.. note:: Some integrations allow specifying these in a standard configuration, otherwise they are generally passed upon
          instantiation of the Sentry client.

.. toctree::
   :maxdepth: 2

   celery
   django
   flask
   logging
   logbook
   wsgi


Client Settings
---------------

Settings are specified as part of the intialization of the client.

::

    from raven import Client

    client = Client(servers=['http://sentry.local/store/'])


name
~~~~

This will override the ``server_name`` value for this installation. Defaults to ``socket.gethostname()``.

::

    name = 'sentry_rocks_' + socket.gethostname()

exclude_paths
~~~~~~~~~~~~~

Extending this allow you to ignore module prefixes when we attempt to discover which function an error comes from (typically a view)

::

    exclude_paths = [
        'django',
        'sentry',
        'raven',
        'lxml.objectify',
    ]

include_paths
~~~~~~~~~~~~~

For example, in Django this defaults to your list of ``INSTALLED_APPS``, and is used for drilling down where an exception is located

::

    include_paths = [
        'django',
        'sentry',
        'raven',
        'lxml.objectify',
    ]

list_max_length
~~~~~~~~~~~~~~~

The maximum number of items a list-like container should store.

If an iterable is longer than the specified length, the left-most elements up to length will be kept.

.. note:: This affects sets as well, which are unordered.

::

    list_max_length = 50

string_max_length
~~~~~~~~~~~~~~~~~

The maximum characters of a string that should be stored.

If a string is longer than the given length, it will be truncated down to the specified size.

::

    list_max_length = 200

auto_log_stacks
~~~~~~~~~~~~~~~

Should Raven automatically log frame stacks (including locals) all calls as it would for exceptions.

::

    auto_log_stacks = True

timeout
~~~~~~~

If supported, the timeout value for sending messages to remote.

::

    timeout = 5