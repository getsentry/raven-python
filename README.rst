.. image:: https://sentry.io/_static/getsentry/images/branding/png/sentry-horizontal-black.png
    :target: https://sentry.io"
    :align: center
    :alt: Sentry website


Raven - Sentry for Python
=========================

.. image:: https://img.shields.io/pypi/v/raven.svg
    :target: https://pypi.python.org/pypi/raven
    :alt: PyPi page link -- version

.. image:: https://travis-ci.org/getsentry/raven-python.svg?branch=master
    :target: https://travis-ci.org/getsentry/raven-python

.. image:: https://img.shields.io/pypi/l/raven.svg
    :target: https://pypi.python.org/pypi/raven
    :alt: PyPi page link -- MIT licence

.. image:: https://img.shields.io/pypi/pyversions/raven.svg
    :target: https://pypi.python.org/pypi/raven
    :alt: PyPi page link -- Python versions

.. image:: https://codeclimate.com/github/getsentry/raven-python/badges/gpa.svg
   :target: https://codeclimate.com/github/codeclimate/codeclimate
   :alt: Code Climate


Raven is the official Python client for `Sentry <http://getsentry.com/>`_, officially supports
Python 2.6–2.7 & 3.3–3.7, and runs on PyPy and Google App Engine.

It tracks errors and exceptions that happen during the
execution of your application and provides instant notification with detailed
information needed to prioritize, identify, reproduce and fix each issue.

It provides full out-of-the-box support for many of the popular python frameworks, including
Django, and Flask. Raven also includes drop-in support for any WSGI-compatible
web application.

Your application doesn't live on the web? No problem! Raven is easy to use in
any Python application.

For more information, see our `python documentation <https://docs.getsentry.com/hosted/clients/python/>`_.


Features
--------

- Automatically report (un)handled exceptions and errors
- Send customized diagnostic data
- Process and sanitize data before sending it over the network


Quickstart
----------

It's really easy to get started with Raven. After you complete setting up a project in Sentry,
you’ll be given a value which we call a DSN, or Data Source Name. You will need it to configure the client.


Install the latest package with *pip* and configure the client::

    pip install raven --upgrade

Create a client and capture an exception:

.. sourcecode:: python

    from raven import Client

    client = Client('___DSN___')

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()


Raven Python is more than that however. Checkout our `python documentation <https://docs.getsentry.com/hosted/clients/python/>`_.


Contributing
------------

Raven is under active development and contributions are more than welcome!
There are many ways to contribute:

* Report bugs on our `issue tracker <http://github.com/getsentry/raven-python/issues>`. Don't forget
to read how you can make `awesome bug reports` to make it easier for us to fix them.
* Fix bugs on our issue tracker. Take a look at our `contribution guidelines`.

TBD..

Running tests
-------------

TBD...


Resources
---------

* `Documentation <https://docs.getsentry.com/hosted/clients/python/>`_
* `Bug Tracker <http://github.com/getsentry/raven-python/issues>`_
* `Code <http://github.com/getsentry/raven-python>`_
* `Mailing List <https://groups.google.com/group/getsentry>`_
* `IRC <irc://irc.freenode.net/sentry>`_  (irc.freenode.net, #sentry)
* `Travis CI <http://travis-ci.org/getsentry/raven-python>`_


Not using Python? Check out our `SDKs for other platforms <https://docs.sentry.io/#platforms/>`_.
