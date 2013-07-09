# -*- coding: utf-8 -*-

import raven
from raven.utils import get_versions


class TestGetVersions(object):
    def test_exact_match(self):
        versions = get_versions(['raven'])
        assert versions.get('raven') == raven.VERSION

    def test_parent_match(self):
        versions = get_versions(['raven.contrib.django'])
        assert versions.get('raven') == raven.VERSION
