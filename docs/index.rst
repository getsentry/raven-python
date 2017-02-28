.. sentry:edition:: self

   Raven Python
   ============

.. sentry:edition:: hosted, on-premise

   .. class:: platform-python

   Python
   ======

For pairing Sentry up with Python you can use the Raven for Python
(raven-python) library.  It is the official standalone Python client for
Sentry.  It can be used with any modern Python interpreter be it CPython
2.x or 3.x, PyPy or Jython.  It's an Open Source project and available
under a very liberal BSD license.

Installation
------------

If you haven't already, start by downloading Raven. The easiest way is
with *pip*::

	pip install raven --upgrade

Configuring the Client
----------------------

Settings are specified as part of the initialization of the client.  The
client is a class that can be instanciated with a specific configuration
and all reporting can then happen from the instance of that object.
Typically an instance is created somewhere globally and then imported as
necessary.  For getting started all you need is your DSN:

.. sourcecode:: python

    from raven import Client
    client = Client('___DSN___')

Capture an Error
----------------

The most basic use for raven is to record one specific error that occurs::

    from raven import Client

    client = Client('___DSN___')

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

Adding Context
--------------

Much of the usefulness of Sentry comes from additional context data with
the events.  The Python client makes this very convenient by providing
methods to set thread local context data that is then submitted
automatically with all events.  For instance you can use
:py:meth:`~raven.Client.user_context` to set the information about the
current user:

.. sourcecode:: python

    def handle_request(request):
        client.user_context({
            'email': request.user.email
        })

Deep Dive
---------

Raven Python is more than that however.  To dive deeper into what it does,
how it works and how it integrates into other systems there is more to
discover:

.. toctree::
   :maxdepth: 2
   :titlesonly:

   usage
   advanced
   breadcrumbs
   integrations/index
   transports
   platform-support
   api

.. sentry:edition:: self

   For Developers
   --------------

   .. toctree::
      :maxdepth: 2
      :titlesonly:

      contributing

   Supported Platforms
   -------------------

   - Python 2.6
   - Python 2.7
   - Python 3.2
   - Python 3.3
   - Python 3.4
   - Python 3.5
   - PyPy
   - Google App Engine

   Deprecation Notes
   -----------------

   Milestones releases are 1.3 or 1.4, and our deprecation policy is to a two
   version step. For example, a feature will be deprecated in 1.3, and
   completely removed in 1.4.

   Resources
   ---------

.. sentry:edition:: hosted, on-premise

   Resources:

* `Documentation <https://docs.getsentry.com/hosted/clients/python/>`_
* `Bug Tracker <http://github.com/getsentry/raven-python/issues>`_
* `Code <http://github.com/getsentry/raven-python>`_
* `Mailing List <https://groups.google.com/group/getsentry>`_
* `IRC <irc://irc.freenode.net/sentry>`_  (irc.freenode.net, #sentry)
