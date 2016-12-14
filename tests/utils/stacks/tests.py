# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os.path

from mock import Mock
from raven.utils.compat import iterkeys, PY3
from raven.utils.testutils import TestCase
from raven.utils.stacks import get_stack_info, get_lines_from_file


class Context(object):
    def __init__(self, dict):
        self.dict = dict

    __getitem__ = lambda s, *a: s.dict.__getitem__(*a)
    __setitem__ = lambda s, *a: s.dict.__setitem__(*a)
    iterkeys = lambda s, *a: iterkeys(s.dict, *a)


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
        if PY3:
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


class FailLoader():
    '''
    Recreating the built-in loaders from a fake stack trace was brittle.
    This method ensures its testing the path where the loader is defined
    but fails with known exceptions.
    '''
    def get_source(self, module_name):
        if '.py' in module_name:
            raise ImportError('Cannot load .py files')
        elif '.zip' in module_name:
            raise IOError('Cannot load .zip files')
        else:
            raise ValueError('Invalid file extension')


class GetLineFromFileTest(TestCase):
    def setUp(self):
        self.loader = FailLoader()

    def test_non_ascii_file(self):
        filename = os.path.join(os.path.dirname(__file__), 'utf8_file.txt')
        self.assertEqual(
            get_lines_from_file(filename, 3, 1),
            (['Some code here'], '', ['lorem ipsum']))

    def test_missing_zip_get_source(self):
        filename = 'does_not_exist.zip'
        module = 'not.zip.loadable'
        self.assertEqual(
            get_lines_from_file(filename, 3, 1, self.loader, module),
            (None, None, None))

    def test_missing_get_source(self):
        filename = 'does_not_exist.py'
        module = 'not.py.loadable'
        self.assertEqual(
            get_lines_from_file(filename, 3, 1, self.loader, module),
            (None, None, None))
