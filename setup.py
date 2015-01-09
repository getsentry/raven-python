#!/usr/bin/env python
"""
Raven
=====

Raven is a Python client for `Sentry <http://getsentry.com/>`_. It provides
full out-of-the-box support for many of the popular frameworks, including
`Django <djangoproject.com>`_, `Flask <http://flask.pocoo.org/>`_, and `Pylons
<http://www.pylonsproject.org/>`_. Raven also includes drop-in support for any
`WSGI <http://wsgi.readthedocs.org/>`_-compatible web application.
"""

# Hack to prevent stupid "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when running `python
# setup.py test` (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
for m in ('multiprocessing', 'billiard'):
    try:
        __import__(m)
    except ImportError:
        pass

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

setup_requires = [
    'pytest',
]

dev_requires = [
    'flake8>=2.0,<2.1',
]

unittest2_requires = ['unittest2']
flask_requires = [
    'Flask>=0.8',
    'blinker>=1.1',
]

flask_tests_requires = [
    'Flask-Login>=0.2.0',
]

webpy_tests_requires = [
    'paste',
    'web.py',
]

# If it's python3, remove unittest2 & web.py
if sys.version_info[0] == 3:
    unittest2_requires = []
    webpy_tests_requires = []

if sys.version_info >= (3, 3):
    aiohttp_requires = ['aiohttp']
else:
    aiohttp_requires = []


tests_require = [
    'bottle',
    'celery>=2.5',
    'Django>=1.4',
    'django-celery>=2.5',
    'exam>=0.5.2',
    'logbook',
    'mock',
    'nose',
    'pep8',
    'pytz',
    'pytest',
    'pytest-cov>=1.4',
    'pytest-django',
    'requests',
    'tornado',
    'webob',
    'webtest',
    'anyjson',
] + (aiohttp_requires + flask_requires + flask_tests_requires +
     unittest2_requires + webpy_tests_requires)


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='raven',
    version='5.2.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/getsentry/raven-python',
    description='Raven is a client for Sentry (https://www.getsentry.com)',
    long_description=__doc__,
    packages=find_packages(exclude=("tests", "tests.*",)),
    zip_safe=False,
    extras_require={
        'flask': flask_requires,
        'tests': tests_require,
        'dev': dev_requires,
    },
    license='BSD',
    tests_require=tests_require,
    cmdclass={'test': PyTest},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'raven = raven.scripts.runner:main',
        ],
        'paste.filter_app_factory': [
            'raven = raven.contrib.paste:sentry_filter_factory',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
)
