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

tests_require = [
    'blinker>=1.1',
    'celery>=2.5',
    'Django>=1.2,<1.5',
    'django-celery>=2.5',
    'django-nose',
    'gevent',
    'Flask>=0.8',
    'logbook',
    'nose',
    'mock',
    'pep8',
    'unittest2',
    'webob',
    'zerorpc>=0.2.0',
    'pytz'
]

install_requires = [
    'simplejson',
]

setup(
    name='raven',
    version='2.0.7',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/getsentry/raven-python',
    description='Raven is a client for Sentry (https://www.getsentry.com)',
    long_description=__doc__,
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
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
        'Topic :: Software Development'
    ],
)
