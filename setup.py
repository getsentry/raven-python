#!/usr/bin/env python
"""
Raven
======

Raven is a Python client for `Sentry <http://aboutsentry.com/>`_. It provides
full out-of-the-box support for many of the popular frameworks, including
Django, and Flask. Raven also includes drop-in support for any WSGI-compatible
web application.
"""

from setuptools import setup, find_packages

tests_require = [
    'blinker>=1.1',
    'celery',
    'Django>=1.2,<1.4',
    'django-celery',
    'django-nose',
    'Flask>=0.8',
    'logbook',
    'nose',
    'mock',
    'sentry>=2.0.0',
    'unittest2',
    'webob',
]

install_requires = [
    'simplejson',
]

setup(
    name='raven',
    version='1.4.5',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/dcramer/raven',
    description='Raven is a client for Sentry',
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
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
