Configuration
=============

.. default-domain:: py

This document describes configuration options available to the Raven
client for the use with Sentry.  It also covers some other important parts
about configuring the environment.


.. _python-client-config:

Configuring the Client
----------------------

Settings are specified as part of the initialization of the client.  The
client is a class that can be instanciated with a specific configuration
and all reporting can then happen from the instance of that object.
Typically an instance is created somewhere globally and then imported as
necessary.

As of Raven 1.2.0, you can now configure all clients through a standard DSN
string. This can be specified as a default using the ``SENTRY_DSN`` environment
variable, as well as passed to all clients by using the ``dsn`` argument.

.. code-block:: python

    from raven import Client

    # Read configuration from the environment
    client = Client()

    # Manually specify a DSN
    client = Client('___DSN___')


A reasonably configured client should generally include a few additional
settings:

.. code-block:: python

    import raven

    client = raven.Client(
        dsn='___DSN___'

        # inform the client which parts of code are yours
        # include_paths=['my.app']
        include_paths=[__name__.split('.', 1)[0]],

        # pass along the version of your application
        # release='1.0.0'
        # release=raven.fetch_package_version('my-app')
        release=raven.fetch_git_sha(os.path.dirname(__file__)),
    )

.. versionadded:: 5.2.0
   The *fetch_package_version* and *fetch_git_sha* helpers.


The Sentry DSN
--------------

.. sentry:edition:: hosted, on-premise

   The most important information is the Sentry DSN.  For information
   about it see :ref:`configure-the-dsn` in the general Sentry docs.

The Python client supports one additional modification to the regular DSN
values which is the choice of the transport.  To select a specific
transport, the DSN needs to be prepended with the name of the transport.
For instance to select the ``gevent`` transport, the following DSN would
be used::

    'gevent+___DSN___'

For more information see :doc:`transports`.

Client Arguments
----------------

The following are valid arguments which may be passed to the Raven client:

.. describe:: dsn

    A Sentry compatible DSN as mentioned before::

        dsn = '___DSN___'

.. describe:: site

    An optional, arbitrary string to identify this client installation::

        site = 'my site name'

.. describe:: name

    This will override the ``server_name`` value for this installation.
    Defaults to ``socket.gethostname()``::

        name = 'sentry_rocks_' + socket.gethostname()

.. describe:: release

    The version of your application. This will map up into a Release in
    Sentry::

        release = '1.0.3'

.. describe:: exclude_paths

    Extending this allow you to ignore module prefixes when we attempt to
    discover which function an error comes from (typically a view)::

        exclude_paths = [
            'django',
            'sentry',
            'raven',
            'lxml.objectify',
        ]

.. describe:: include_paths

    For example, in Django this defaults to your list of ``INSTALLED_APPS``,
    and is used for drilling down where an exception is located::

        include_paths = [
            'django',
            'sentry',
            'raven',
            'lxml.objectify',
        ]

.. describe:: max_list_length

    The maximum number of items a list-like container should store.

    If an iterable is longer than the specified length, the left-most
    elements up to length will be kept.

    .. note:: This affects sets as well, which are unordered.

    ::

        list_max_length = 50

.. describe:: string_max_length

    The maximum characters of a string that should be stored.

    If a string is longer than the given length, it will be truncated down
    to the specified size::

        string_max_length = 200

.. describe:: auto_log_stacks

    Should Raven automatically log frame stacks (including locals) for all
    calls as it would for exceptions::

        auto_log_stacks = True

.. describe:: processors

    A list of processors to apply to events before sending them to the
    Sentry server. Useful for sending additional global state data or
    sanitizing data that you want to keep off of the server::

        processors = (
            'raven.processors.SanitizePasswordsProcessor',
        )

Sanitizing Data
---------------

Several processors are included with Raven to assist in data
sanitiziation. These are configured with the ``processors`` value.

.. data:: raven.processors.SanitizePasswordsProcessor
   :noindex:

   Removes all keys which resemble ``password``, ``secret``, or
   ``api_key`` within stacktrace contexts, HTTP bits (such as cookies,
   POST data, the querystring, and environment), and extra data.

.. data:: raven.processors.RemoveStackLocalsProcessor
   :noindex:

   Removes all stacktrace context variables. This will cripple the
   functionality of Sentry, as you'll only get raw tracebacks, but it will
   ensure no local scoped information is available to the server.

.. data:: raven.processors.RemovePostDataProcessor
   :noindex:

   Removes the ``body`` of all HTTP data.


A Note on uWSGI
---------------

If you're using uWSGI you will need to add ``enable-threads`` to the
default invocation, or you will need to switch off of the threaded default
transport.
