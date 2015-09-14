from __future__ import absolute_import

import os.path
import pytest
import subprocess

from django.conf import settings

from raven.versioning import fetch_git_sha, fetch_package_version
from raven.utils import six


def has_git_requirements():
    return os.path.exists(os.path.join(settings.PROJECT_ROOT, '.git', 'refs', 'heads', 'master'))


@pytest.mark.skipif('not has_git_requirements()')
def test_fetch_git_sha():
    result = fetch_git_sha(settings.PROJECT_ROOT)
    assert result is not None
    assert len(result) == 40
    assert isinstance(result, six.string_types)
    assert result == subprocess.check_output(
        'git rev-parse --verify HEAD', shell=True, cwd=settings.PROJECT_ROOT
    ).strip()


def test_fetch_package_version():
    result = fetch_package_version('raven')
    assert result is not None
    assert isinstance(result, six.string_types)
