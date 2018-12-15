#!/usr/bin/env python
"""
Raven
=====

Raven is a Python client for `Sentry <http://getsentry.com/>`_. It provides
full out-of-the-box support for many of the popular frameworks, including
`Django <djangoproject.com>`_, `Flask <http://flask.pocoo.org/>`_, and `Pylons
<http://www.pylonsproject.org/>`_. Raven also includes drop-in support for any
`WSGI <https://wsgi.readthedocs.io/>`_-compatible web application.
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
import re
import sys
import ast


_version_re = re.compile(r'VERSION\s+=\s+(.*)')

with open('raven/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


install_requires = []
unittest2_requires = ['unittest2']

flask_requires = [
    'Flask>=0.8',
    'blinker>=1.1',
]

flask_tests_requires = [
    'Flask-Login>=0.2.0',
]

sanic_requires = []
sanic_tests_requires = []

webpy_tests_requires = [
    'paste',
    'web.py',
]

# If it's python3, remove unittest2 & web.py.
if sys.version_info[0] == 3:
    unittest2_requires = []
    webpy_tests_requires = []

# If it's Python 3.5+, add Sanic packages.
if sys.version_info >= (3, 5):
    sanic_requires = [
        'blinker>=1.1',
        'sanic>=0.7.0',
    ]
    sanic_tests_requires = ['aiohttp', ]

tests_require = [
    'bottle',
    'celery>=2.5',
    'coverage<4',
    'exam>=0.5.2',
    'flake8==3.5.0',
    'logbook',
    'mock',
    'nose',
    'pytz',
    'pytest>=3.2.0,<3.3.0',
    'pytest-timeout==1.2.1',
    'pytest-xdist==1.18.2',
    'pytest-pythonpath==0.7.2',
    'pytest-cov==2.5.1',
    'pytest-flake8==1.0.0',
    'requests',
    'tornado>=4.1,<5.0',
    'tox',
    'webob',
    'webtest',
    'wheel',
    'anyjson',
    'ZConfig',
] + (
    flask_requires + flask_tests_requires
    + sanic_requires + sanic_tests_requires
    + unittest2_requires + webpy_tests_requires
)


class PyTest(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='raven',
    version=version,
    author='Sentry',
    author_email='hello@getsentry.com',
    url='https://github.com/getsentry/raven-python',
    description='Raven is a client for Sentry (https://getsentry.com)',
    long_description=__doc__,
    packages=find_packages(exclude=("tests", "tests.*",)),
    zip_safe=False,
    extras_require={
        'flask': flask_requires,
        'tests': tests_require,
        ':python_version<"3.2"': ['contextlib2'],
    },
    license='BSD',
    tests_require=tests_require,
    install_requires=install_requires,
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
)
