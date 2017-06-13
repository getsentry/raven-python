# -*- coding: utf-8 -*-

import collections
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

    def test_defaultdict(self):
        orig_d = {'foo': 'bar'}
        d = collections.defaultdict(list)
        d.update(orig_d)
        assert json.dumps(d) == '{"foo": "bar"}'

    def test_tuple_keys(self):
        d = {(1, 2): "tuple_key"}
        assert json.dumps(d) == '{"(1, 2)": "tuple_key"}'

    def test_func_keys(self):
        d = {dir: "func_key"}
        assert json.dumps(d) == '{"<built-in function dir>": "func_key"}'

    def test_frozenset_keys(self):
        key = frozenset([1])
        d = {key: "set_key"}
        # Python 2/3 use different repr formats.
        assert json.dumps(d) == '{"%s": "set_key"}' % repr(key)

    def test_complex_value(self):
        d = {"complex_value": 2+1j}
        assert json.dumps(d) == '{"complex_value": "(2+1j)"}'

    def test_all_together(self):
        fs_key = frozenset([dir])
        d = {
            (dir,): frozenset([2+1j]),
            dir: collections.defaultdict(set),
            fs_key: [2 + 1j],
        }
        # Python 2/3 use different repr formats.
        assert json.dumps(d, sort_keys=True) == \
            '{' \
            '"(<built-in function dir>,)": ["(2+1j)"], ' \
            '"<built-in function dir>": {}, ' \
            '"%s": ["(2+1j)"]' \
            '}' % repr(fs_key)
