# -*- coding: utf-8 -*-

import datetime
import uuid

from raven.utils import json


class TestJSON(object):
    def test_uuid(self):
        res = uuid.uuid4()
        assert json.dumps(res) == '"%s"' % res.hex

    def test_datetime(self):
        res = datetime.datetime(day=1, month=1, year=2011, hour=1, minute=1, second=1)
        assert json.dumps(res) == '"2011-01-01T01:01:01Z"'

    def test_set(self):
        res = set(['foo', 'bar'])
        assert json.dumps(res) in ('["foo", "bar"]', '["bar", "foo"]')

    def test_frozenset(self):
        res = frozenset(['foo', 'bar'])
        assert json.dumps(res) in ('["foo", "bar"]', '["bar", "foo"]')
