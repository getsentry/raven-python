from __future__ import absolute_import

import os.path
import pytest
import subprocess

from conftest import project_root
from raven.utils.compat import string_types
from raven.versioning import fetch_git_sha, fetch_package_version


def has_git_requirements(project_root):
    return os.path.exists(os.path.join(project_root, '.git', 'refs', 'heads', 'master'))


# Python 2.6 does not contain subprocess.check_output
def check_output(cmd, **kwargs):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        **kwargs
    ).communicate()[0]


@pytest.mark.skipif(not has_git_requirements(project_root()),
                    reason='unable to detect git repository')
def test_fetch_git_sha(project_root):
    result = fetch_git_sha(project_root)
    assert result is not None
    assert len(result) == 40
    assert isinstance(result, string_types)
    assert result == check_output(
        'git rev-parse --verify HEAD', shell=True, cwd=project_root
    ).decode('latin1').strip()


def test_fetch_package_version():
    result = fetch_package_version('raven')
    assert result is not None
    assert isinstance(result, string_types)
