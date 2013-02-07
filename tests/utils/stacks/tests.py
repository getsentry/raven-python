# -*- coding: utf-8 -*-

from mock import Mock
from unittest2 import TestCase

from raven.utils.stacks import get_culprit, get_stack_info


class Context(object):
    def __init__(self, dict):
        self.dict = dict

    __getitem__ = lambda s, *a: s.dict.__getitem__(*a)
    __setitem__ = lambda s, *a: s.dict.__setitem__(*a)
    iterkeys = lambda s, *a: s.dict.iterkeys(*a)


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
        assert culprit == None

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
        self.assertEquals(len(results), 1)
        result = results[0]
        self.assertTrue('vars' in result)
        vars = result['vars']
        self.assertTrue(isinstance(vars, dict))
        self.assertTrue('foo' in vars)
        self.assertEquals(vars['foo'], 'bar')
        self.assertTrue('biz' in vars)
        self.assertEquals(vars['biz'], 'baz')
