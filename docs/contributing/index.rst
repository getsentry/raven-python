Contributing
============

Want to contribute back to Sentry? This page describes the general development flow,
our philosophy, the test suite, and issue tracking.

(Though it actually doesn't describe all of that, yet)

Setting up an Environment
-------------------------

Sentry is designed to run off of setuptools with minimal work. Because of this
setting up a development environment requires only a few steps.

The first thing you're going to want to do, is build a virtualenv and install
any base dependancies.

::

    virtualenv ~/.virtualenvs/raven
    source ~/.virtualenvs/raven/bin/activate
    make

That's it :)

Running the Test Suite
----------------------

The test suite is also powered off of py.test, and can be run in a number of ways. Usually though,
you'll just want to use our helper method to make things easy:

::

    make test


Contributing Back Code
----------------------

Ideally all patches should be sent as a pull request on GitHub, and include tests. If you're fixing a bug or making a large change the patch **must** include test coverage.

You can see a list of open pull requests (pending changes) by visiting https://github.com/getsentry/raven-python/pulls
