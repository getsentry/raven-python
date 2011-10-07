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


Client Settings
---------------

Settings are specified as part of the intialization of the client. For example::

    from raven import Client

    client = Client(remote_urls=['http://sentry.local/store/'])

name
~~~~

This will override the ``server_name`` value for this installation. Defaults to ``socket.gethostname()``.

exclude_paths
~~~~~~~~~~~~~

Extending this allow you to ignore module prefixes when we attempt to discover which function an error comes from (typically a view)

include_paths
~~~~~~~~~~~~~

For example, in Django this defaults to your list of ``INSTALLED_APPS``, and is used for drilling down where an exception is located

list_max_length
~~~~~~~~~~~~~~~

The maximum number of items a list-like container should store. Defaults to ``50``.

string_max_length
~~~~~~~~~~~~~~~~~

The maximum characters of a string that should be stored. Defaults to ``200``.

auto_log_stacks
~~~~~~~~~~~~~~~

Should Raven automatically log frame stacks (including locals) for ``create_from_record`` (``logging``) calls as it would for exceptions. Defaults to ``False``.
