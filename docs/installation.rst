Installation
============

If you haven't already, start by downloading Raven. The easiest way is
with *pip*::

	pip install raven --upgrade

Or alternatively with *setuptools*::

	easy_install -U raven

If you want to use the latest git version you can get it from `the github
repository <https://github.com/getsentry/raven-python>`_::

    git clone https://github.com/getsentry/raven-python
    pip install raven-python

Certain additional features can be installed by defining the feature when
``pip`` installing it.  For instance to install all dependencies needed to
use the Flask integration, you can depend on ``raven[flask]``::

    pip install raven[flask]

For more information refer to the individual integration documentation.
