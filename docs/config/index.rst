Configuration
=============

This document describes configuration options available to Sentry.


Configuring the Client
----------------------

Settings are specified as part of the initialization of the client.

As of Raven 1.2.0, you can now configure all clients through a standard DSN
string. This can be specified as a default using the ``SENTRY_DSN`` environment
variable, as well as passed to all clients by using the ``dsn`` argument.

.. code-block:: python

    from raven import Client

    # Read configuration from the environment
    client = Client()

    # Manually specify a DSN
    client = Client('http://public:secret@example.com/1')


A reasonably configured client should generally include a few additional settings:

.. code-block:: python

    import raven

    client = raven.Client(
        dsn='http://public:secret@example.com/1'

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

The DSN can be found in Sentry by navigation to Account -> Projects -> [Project Name] -> [Member Name]. Its template resembles the following::

    '{PROTOCOL}://{PUBLIC_KEY}:{SECRET_KEY}@{HOST}/{PATH}{PROJECT_ID}'

It is composed of six important pieces:

* The Protocol used. This can be one of the following: http, https, or udp.

* The public and secret keys to authenticate the client.

* The hostname of the Sentry server.

* An optional path if Sentry is not located at the webserver root. This is specific to HTTP requests.

* The project ID which the authenticated user is bound to.

.. note::

   Protocol may also contain transporter type: gevent+http, gevent+https, twisted+http, tornado+http, eventlet+http, eventlet+https

   For *Python 3.3+* also available: aiohttp+http and aiohttp+https

Client Arguments
----------------

The following are valid arguments which may be passed to the Raven client:

dsn
~~~

A sentry compatible DSN.

::

    dsn = 'http://public:secret@example.com/1'

project
~~~~~~~

Set this to your Sentry project ID. The default value for installations is ``1``.

::

    project = 1


public_key
~~~~~~~~~~

Set this to the public key of the project member which will authenticate as the
client. You can find this information on the member details page of your project
within Sentry.

::

    public_key = 'fb9f9e31ea4f40d48855c603f15a2aa4'


secret_key
~~~~~~~~~~

Set this to the secret key of the project member which will authenticate as the
client. You can find this information on the member details page of your project
within Sentry.

::

    secret_key = '6e968b3d8ba240fcb50072ad9cba0810'

site
~~~~

An optional, arbitrary string to identify this client installation.

::

    site = 'my site name'


name
~~~~

This will override the ``server_name`` value for this installation. Defaults to ``socket.gethostname()``.

::

    name = 'sentry_rocks_' + socket.gethostname()


release
~~~~~~~~

The version of your application. This will map up into a Release in Sentry.

::

    release = '1.0.3'


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

    string_max_length = 200

auto_log_stacks
~~~~~~~~~~~~~~~

Should Raven automatically log frame stacks (including locals) for all calls as
it would for exceptions.

::

    auto_log_stacks = True


processors
~~~~~~~~~~

A list of processors to apply to events before sending them to the Sentry server. Useful for sending
additional global state data or sanitizing data that you want to keep off of the server.

::

    processors = (
        'raven.processors.SanitizePasswordsProcessor',
    )

Sanitizing Data
---------------

Several processors are included with Raven to assist in data sanitiziation. These are configured with the
``processors`` value.

.. data:: raven.processors.SanitizePasswordsProcessor

   Removes all keys which resemble ``password``, ``secret``, or ``api_key``
   within stacktrace contexts, HTTP bits (such as cookies, POST data,
   the querystring, and environment), and extra data.

.. data:: raven.processors.RemoveStackLocalsProcessor

   Removes all stacktrace context variables. This will cripple the functionality of Sentry, as you'll only
   get raw tracebacks, but it will ensure no local scoped information is available to the server.

.. data:: raven.processors.RemovePostDataProcessor

   Removes the ``body`` of all HTTP data.


A Note on uWSGI
---------------

If you're using uWSGI you will need to add ``enable-threads`` to the default invocation, or you will need to switch off of the threaded transport.
