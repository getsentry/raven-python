#!/usr/bin/env python
"""
Raven
======

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
import sys

dev_requires = [
    'flake8>=1.6,<2.0',
]

unittest2_requires = ['unittest2']
flask_requires = [
    'Flask>=0.8',
    'blinker>=1.1',
]

# If it's python3, remove flask & unittest2
if sys.version_info[0] == 3:
    flask_requires = []
    unittest2_requires = []


tests_require = [
    'celery>=2.5',
    'Django>=1.2',
    'django-celery>=2.5',
    'exam>=0.5.2',
    'logbook',
    'mock',
    'nose',
    'pep8',
    'pytz',
    'pytest',
    'pytest-django-lite',
    'tornado',
    'webob',
    'anyjson',
] + flask_requires + unittest2_requires

setup(
    name='raven',
    version='3.3.3',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/getsentry/raven-python',
    description='Raven is a client for Sentry (https://www.getsentry.com)',
    long_description=__doc__,
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    extras_require={
        'flask': flask_requires,
        'tests': tests_require,
        'dev': dev_requires,
    },
    test_suite='runtests.runtests',
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
        'Topic :: Software Development',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.2',
    ],
)
