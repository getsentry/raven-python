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


class StackTest(TestCase):
    def test_get_culprit_bad_module(self):
        culprit = get_culprit([{
            'module': None,
            'function': 'foo',
        }])
        self.assertEquals(culprit, '<unknown>.foo')

        culprit = get_culprit([{
            'module': 'foo',
            'function': None,
        }])
        self.assertEquals(culprit, 'foo.<unknown>')

        culprit = get_culprit([{
        }])
        self.assertEquals(culprit, '<unknown>.<unknown>')

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

        frames = [frame]
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
