.. raw:: html

    <p align="center">

.. image:: docs/_static/logo.png
    :target: https://sentry.io
    :align: center
    :width: 116
    :alt: Sentry website

.. raw:: html

    </p>

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
   :target: https://codeclimate.com/github/getsentry/raven-python
   :alt: Code Climate


Raven is the official Python client for `Sentry`_, officially supports
Python 2.6–2.7 & 3.3–3.7, and runs on PyPy and Google App Engine.

It tracks errors and exceptions that happen during the
execution of your application and provides instant notification with detailed
information needed to prioritize, identify, reproduce and fix each issue.

It provides full out-of-the-box support for many of the popular python frameworks, including
Django, and Flask. Raven also includes drop-in support for any WSGI-compatible
web application.

Your application doesn't live on the web? No problem! Raven is easy to use in
any Python application.

For more information, see our `Python Documentation`_ for framework integrations and other goodies.


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

Create a client and capture an example exception:

.. sourcecode:: python

    from raven import Client

    client = Client('___DSN___')

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()


Raven Python is more than that however. Checkout our `Python Documentation`_.


Contributing
------------

Raven is under active development and contributions are more than welcome!
There are many ways to contribute:

* Join in on discussions on our `Mailing List`_ or in our `IRC Channel`_.

* Report bugs on our `Issue Tracker`_.

* Submit a pull request!


Resources
---------

* `Sentry`_
* `Python Documentation`_
* `Issue Tracker`_
* `Code`_ on Github
* `Mailing List`_
* `IRC Channel`_ (irc.freenode.net, #sentry)
* `Travis CI`_

.. _Sentry: https://getsentry.com/
.. _Python Documentation: https://docs.getsentry.com/hosted/clients/python/
.. _SDKs for other platforms: https://docs.sentry.io/#platforms
.. _Issue Tracker: https://github.com/getsentry/raven-python/issues
.. _Code: https://github.com/getsentry/raven-python
.. _Mailing List: https://groups.google.com/group/getsentry
.. _IRC Channel: irc://irc.freenode.net/sentry
.. _Travis CI: http://travis-ci.org/getsentry/raven-python





Not using Python? Check out our `SDKs for other platforms`_.
