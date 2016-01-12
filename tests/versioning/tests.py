from __future__ import absolute_import

import os.path
import pytest
import subprocess
import six

from django.conf import settings

from raven.versioning import fetch_git_sha, fetch_package_version


def has_git_requirements():
    return os.path.exists(os.path.join(settings.PROJECT_ROOT, '.git', 'refs', 'heads', 'master'))


# Python 2.6 does not contain subprocess.check_output
def check_output(cmd, **kwargs):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        **kwargs
    ).communicate()[0]


@pytest.mark.skipif('not has_git_requirements()')
def test_fetch_git_sha():
    result = fetch_git_sha(settings.PROJECT_ROOT)
    assert result is not None
    assert len(result) == 40
    assert isinstance(result, six.string_types)
    assert result == check_output(
        'git rev-parse --verify HEAD', shell=True, cwd=settings.PROJECT_ROOT
    ).decode('latin1').strip()


def test_fetch_package_version():
    result = fetch_package_version('raven')
    assert result is not None
    assert isinstance(result, six.string_types)
