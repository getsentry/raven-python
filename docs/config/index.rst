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
   pylons
   logging
   logbook
   wsgi


Congiruing the Client
---------------------

Settings are specified as part of the intialization of the client.

As of Raven 1.2.0, you can now configure all clients through a standard DSN
string. This can be specified as a default using the ``SENTRY_DSN`` environment
variable, as well as passed to all clients by using the ``dsn`` argument.

::

    from raven import Client

    # Read configuration from the environment
    client = Client()

    # Manually specify a DSN
    client = Client('http://public:secret@example.com/1')

    # Configure a client manually
    client = Client(
        servers=['http://sentry.local/api/store/'],
        public_key='public_key',
        secret_key='secret_key',
        project=1,
    )


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

    public_key = '6e968b3d8ba240fcb50072ad9cba0810'

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