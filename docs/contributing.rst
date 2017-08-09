Contributing
============

Want to contribute back to Sentry? This page describes the general development flow,
our philosophy, the test suite, and issue tracking.

There are many ways to you can help, either by submitting bug reports, improving the
documentation, or submitting a patch. This document describes how to get the
test suite running for the Python SDK.

Setting up an Environment
-------------------------

There are several ways of setting up a development environment. If you want to ensure
your changes work across all environments and integrations that Raven supports,
the easiest way to run one or more jobs from test suite matrix is using a virtualenv
management and test command line tool called `Tox`_,

It is also recommended to have the Python versions you are targeting installed on your
system. There are several tools that help you manage several Python installations,
like `Pyenv`_ or `Pythonz`_, but you can also install them manually by downloading them
from the Python.org website or installing them from repositories depending on your
operating system.

Once you have the Python versions you are going to work with, you have to install `Tox`.
The easiest way of installing `Tox` is by running `pip install tox` into your
default Python installation.

Running the tests
-----------------

Running the tests is easy: just run `tox` from the command line and it will take care of
creating all the necessary virtualenvs and running all the environments defined in the `tox.ini`
file.

During development you might want to run only a certain environment, which can be done by
passing the `-e ENV` to tox, for example:

.. code-block:: bash

    $ tox -e py35-django19

which would run the Python3.5 environment and the Django integration tests with Django 1.9.
You can list all the defined environments with `tox --listenvs`, or fall into the Python debugger
on any raised exception by using `tox --pdb`. Please refer to the Tox Documentation for additional
information.


Contributing Back Code
----------------------

Ideally all patches should be sent as a pull request on GitHub, and include tests.
If you're fixing a bug or making a large change the patch **must** include test coverage.

You can see a list of open pull requests (pending changes) by visiting our `Github Pull Request` page.
Every pull requests triggers a test build on our Travis CI where you can verify that
all tests pass.

Notes
-----

In order to use Pyenv with Tox, create a `.python-version` file similar to the
`.python-version-example` in the project root.


.. _Sentry: https://getsentry.com
.. _Github Pull Request: https://github.com/getsentry/raven-python/pulls
.. _Tox: https://tox.readthedocs.io
.. _Pythonz: https://github.com/saghul/pythonz
.. _Pyenv: https://github.com/pyenv/pyenv