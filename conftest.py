from __future__ import absolute_import

import os.path
import pytest
import sys

collect_ignore = [
    'tests/contrib/awslambda'
]

if sys.version_info[0] > 2:
    if sys.version_info[1] < 3:
        collect_ignore.append('tests/contrib/flask')
    if sys.version_info[1] == 2:
        collect_ignore.append('tests/handlers/logbook')

try:
    import gevent  # NOQA
except ImportError:
    collect_ignore.append('tests/transport/gevent')

try:
    import web  # NOQA
except ImportError:
    collect_ignore.append('tests/contrib/webpy')

try:
    import django  # NOQA
except ImportError:
    django = None
    collect_ignore.append('tests/contrib/django')

try:
    import Sanic  # NOQA
except ImportError:
    collect_ignore.append('tests/contrib/sanic')

try:
    import tastypie  # NOQA
except ImportError:
    collect_ignore.append('tests/contrib/django/test_tastypie.py')


use_djcelery = True
try:
    import djcelery  # NOQA
    # INSTALLED_APPS.append('djcelery')
except ImportError:
    use_djcelery = False


def pytest_runtest_teardown(item):
    if django:
        from raven.contrib.django.models import client
        client.events = []


@pytest.fixture
def project_root():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def mytest_model():

    from tests.contrib.django.models import MyTestModel
    return MyTestModel


@pytest.fixture(scope='function', autouse=False)
def user_instance(request, admin_user):
    request.cls.user = admin_user


@pytest.fixture(autouse=True)
def has_git_requirements(request, project_root):
    if request.node.get_marker('has_git_requirements'):
        if not os.path.exists(os.path.join(project_root, '.git', 'refs', 'heads', 'master')):
            pytest.skip('skipped test as project is not a git repo')
