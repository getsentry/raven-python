Contributing
============

Want to contribute back to Sentry? This page describes the general development flow,
our philosophy, the test suite, and issue tracking.

(Though it actually doesn't describe all of that, yet)

Setting up an Environment
-------------------------

Sentry is designed to run off of setuptools with minimal work. Because of this
setting up a development environment for Sentry requires only a few steps.

The first thing you're going to want to do, is build a virtualenv and install
any base dependancies.

::

    virtualenv ~/.virtualenvs/raven
    source ~/.virtualenvs/raven/bin/activate
    make

Running the Test Suite
----------------------

The test suite is also powered off of setuptools, and can be run in two fashions. The
easiest is to simply use setuptools and it's ``test`` command. This will handle installing
any dependancies you're missing automatically.

::

    make test


Contributing Back Code
----------------------

Ideally all patches should be sent as a pull request on GitHub, and include tests. If you're fixing a bug or making a large change the patch **must** include test coverage.

You can see a list of open pull requests (pending changes) by visiting https://github.com/getsentry/raven-python/pulls
