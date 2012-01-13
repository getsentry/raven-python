#!/usr/bin/env python

import sys

try:
    from setuptools import setup, find_packages, Command
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages, Command

tests_require = [
    'Django>=1.2,<1.4',
    'django-celery',
    'celery',

    'blinker>=1.1',
    'Flask>=0.8',
    'django-sentry',
    'django-nose',
    'nose',
    'unittest2',
]

install_requires = [
    'simplejson',
]

if sys.version_info[:2] < (2, 5):
    install_requires.append('uuid')

setup(
    name='raven',
    version='0.7.1',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/dcramer/raven',
    description = 'Exception Logging to a Database in Django',
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
