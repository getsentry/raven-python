# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six

from mock import Mock
from raven.utils.testutils import TestCase

from raven.utils.stacks import get_culprit, get_stack_info, get_lines_from_file


class Context(object):
    def __init__(self, dict):
        self.dict = dict

    __getitem__ = lambda s, *a: s.dict.__getitem__(*a)
    __setitem__ = lambda s, *a: s.dict.__setitem__(*a)
    iterkeys = lambda s, *a: six.iterkeys(s.dict, *a)


class GetCulpritTest(TestCase):
    def test_empty_module(self):
        culprit = get_culprit([{
            'module': None,
            'function': 'foo',
        }])
        assert culprit == '? in foo'

    def test_empty_function(self):
        culprit = get_culprit([{
            'module': 'foo',
            'function': None,
        }])
        assert culprit == 'foo in ?'

    def test_no_module_or_function(self):
        culprit = get_culprit([{}])
        assert culprit is None

    def test_all_params(self):
        culprit = get_culprit([{
            'module': 'package.name',
            'function': 'foo',
        }])
        assert culprit == 'package.name in foo'


class GetStackInfoTest(TestCase):
    def test_bad_locals_in_frame(self):
        frame = Mock()
        frame.f_locals = Context({
            'foo': 'bar',
            'biz': 'baz',
        })
        frame.f_lineno = 1
        frame.f_globals = {}
        frame.f_code.co_filename = __file__
        frame.f_code.co_name = __name__

        frames = [(frame, 1)]
        results = get_stack_info(frames)
        assert len(results['frames']) == 1
        result = results['frames'][0]
        assert 'vars' in result
        if six.PY3:
            expected = {
                "foo": "'bar'",
                "biz": "'baz'",
            }
        else:
            expected = {
                "foo": "u'bar'",
                "biz": "u'baz'",
            }
        assert result['vars'] == expected

    def test_frame_allowance(self):
        frames = []
        for x in range(10):
            frame = Mock()
            frame.f_locals = {'k': 'v'}
            frame.f_lineno = None
            frame.f_globals = {}
            frame.f_code.co_filename = str(x)
            frame.f_code.co_name = __name__
            frames.append((frame, 1))

        results = get_stack_info(frames, frame_allowance=4)
        assert len(results['frames']) == 10
        assert results['frames'][0]['filename'] == '0'
        assert results['frames'][1]['filename'] == '1'
        for idx, frame in enumerate(results['frames'][2:8]):
            assert frame['filename'] == str(idx + 2)
            assert 'vars' not in frame
        assert results['frames'][8]['filename'] == '8'
        assert results['frames'][9]['filename'] == '9'


class GetLineFromFileTest(TestCase):
    def test_non_ascii_file(self):
        import os.path
        filename = os.path.join(os.path.dirname(__file__), 'utf8_file.txt')
        self.assertEqual(
            get_lines_from_file(filename, 3, 1),
            (['Some code here'], '', ['lorem ipsum']))
