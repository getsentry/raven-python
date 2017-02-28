Advanced Usage
==============

This covers some advanced usage scenarios for raven Python.

Alternative Installations
-------------------------

If you want to use the latest git version you can get it from `the github
repository <https://github.com/getsentry/raven-python>`_::

    git clone https://github.com/getsentry/raven-python
    pip install raven-python

Certain additional features can be installed by defining the feature when
``pip`` installing it.  For instance to install all dependencies needed to
use the Flask integration, you can depend on ``raven[flask]``::

    pip install raven[flask]

For more information refer to the individual integration documentation.

.. _python-client-config:

Configuring the Client
----------------------

Settings are specified as part of the initialization of the client.  The
client is a class that can be instantiated with a specific configuration
and all reporting can then happen from the instance of that object.
Typically an instance is created somewhere globally and then imported as
necessary.

.. code-block:: python

    from raven import Client

    # Read configuration from the ``SENTRY_DSN`` environment variable
    client = Client()

    # Manually specify a DSN
    client = Client('___DSN___')


A reasonably configured client should generally include a few additional
settings:

.. code-block:: python

    import os
    import raven

    client = raven.Client(
        dsn='___DSN___',

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


Client Arguments
----------------

The following are valid arguments which may be passed to the Raven client:

.. describe:: dsn

    A Sentry compatible DSN as mentioned before::

        dsn = '___DSN___'

.. describe:: transport

    The HTTP transport class to use. By default this is an asynchronous worker
    thread that runs in-process.

    For more information see :doc:`transports`.

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

.. describe:: environment

    The environment your application is running in::

        environment = 'staging'

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

.. describe:: ignore_exceptions

    A list of exceptions to ignore::

        ignore_exceptions = [
            'Http404',
            'django.exceptions.http.Http404',
            'django.exceptions.*',
        ]

.. describe:: list_max_length

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

.. describe:: raven.processors.SanitizePasswordsProcessor

   Removes all keys which resemble ``password``, ``secret``, or
   ``api_key`` within stacktrace contexts, HTTP bits (such as cookies,
   POST data, the querystring, and environment), and extra data.

.. describe:: raven.processors.RemoveStackLocalsProcessor

   Removes all stacktrace context variables. This will cripple the
   functionality of Sentry, as you'll only get raw tracebacks, but it will
   ensure no local scoped information is available to the server.

.. describe:: raven.processors.RemovePostDataProcessor

   Removes the ``body`` of all HTTP data.

Custom Grouping Behavior
------------------------

In some cases you may see issues where Sentry groups multiple events together
when they should be separate entities. In other cases, Sentry simply doesn't
group events together because they're so sporadic that they never look the same.

Both of these problems can be addressed by specifying the ``fingerprint``
attribute.

For example, if you have HTTP 404 (page not found) errors, and you'd prefer they
deduplicate by taking into account the URL:

.. code-block:: python

    client.captureException(fingerprint=['{{ default }}', 'http://my-url/'])

.. sentry:edition:: hosted, on-premise

    For more information, see :ref:`custom-grouping`.

A Note on uWSGI
---------------

If you're using uWSGI you will need to add ``enable-threads`` to the
default invocation, or you will need to switch off of the threaded default
transport.
