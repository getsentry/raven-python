import fnmatch
import os

from subprocess import call
from raven.utils.testutils import BaseTestCase as TestCase


ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'raven'))


def find_files(root, pattern='*'):
    matches = []
    for root, _, filenames in os.walk(root):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches


class FutureImportsTest(TestCase):
    def test_absolute_import(self):
        string = 'from __future__ import absolute_import'
        kwargs = {
            'stdout': open('/dev/null', 'a'),
            'stderr': open('/dev/null', 'a'),
        }
        for filename in find_files(ROOT, '*.py'):
            assert not call(['grep', string, filename], **kwargs), \
                "Missing %r in %s" % (string, filename[len(ROOT) - 5:])
