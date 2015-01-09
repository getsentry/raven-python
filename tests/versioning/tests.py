from __future__ import absolute_import

from django.conf import settings

from raven.versioning import fetch_git_sha, fetch_package_version


def test_fetch_git_sha():
    result = fetch_git_sha(settings.PROJECT_ROOT)
    assert result is not None
    assert len(result) == 40
    assert isinstance(result, basestring)


def test_fetch_package_version():
    result = fetch_package_version('raven')
    assert result is not None
    assert isinstance(result, basestring)
