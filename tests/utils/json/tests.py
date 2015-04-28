# -*- coding: utf-8 -*-

import datetime
import uuid
from decimal import Decimal
from raven.utils.testutils import TestCase

from raven.utils import json


class JSONTest(TestCase):
    def test_uuid(self):
        res = uuid.uuid4()
        json.dumps(res) == '"%s"' % res.hex

    def test_datetime(self):
        res = datetime.datetime(day=1, month=1, year=2011, hour=1, minute=1, second=1)
        assert json.dumps(res) == '"2011-01-01T01:01:01Z"'

    def test_set(self):
        res = set(['foo', 'bar'])
        assert json.dumps(res) in ('["foo", "bar"]', '["bar", "foo"]')

    def test_frozenset(self):
        res = frozenset(['foo', 'bar'])
        assert json.dumps(res) in ('["foo", "bar"]', '["bar", "foo"]')

    def test_unknown_type(self):

        class Unknown(object):
            def __repr__(self):
                return 'Unknown object'

        obj = Unknown()
        assert json.dumps(obj) == '"Unknown object"'

    def test_decimal(self):
        d = {'decimal': Decimal('123.45')}
        assert json.dumps(d) == '{"decimal": "Decimal(\'123.45\')"}'
