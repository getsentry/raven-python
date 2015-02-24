from __future__ import absolute_import

import os.path
try:
    import pkg_resources
except ImportError:
    # pkg_resource is not available on Google App Engine
    pkg_resources = None

from .exceptions import InvalidGitRepository

__all__ = ('fetch_git_sha', 'fetch_package_version')


def fetch_git_sha(path, head='master'):
    """
    >>> fetch_git_sha(os.path.dirname(__file__))
    """
    revision_file = os.path.join(path, '.git', 'refs', 'heads', head)
    if not os.path.exists(revision_file):
        if not os.path.exists(os.path.join(path, '.git')):
            raise InvalidGitRepository('%s does not seem to be the root of a git repository' % (path,))
        raise InvalidGitRepository('Unable to find ref to head "%s" in repository' % (head,))

    fh = open(revision_file, 'r')
    try:
        return fh.read().strip()
    finally:
        fh.close()


def fetch_package_version(dist_name):
    """
    >>> fetch_package_version('sentry')
    """
    if pkg_resources is None:
        raise NotImplementedError('pkg_resources is not available on this Python install')
    dist = pkg_resources.get_distribution(dist_name)
    return dist.version
