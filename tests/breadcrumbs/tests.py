import sys
import logging

from raven.utils.testutils import TestCase

from raven.base import Client
from raven import breadcrumbs

from io import StringIO


class DummyClass(object):
    def dummy_method(self):
        pass


class BreadcrumbTestCase(TestCase):

    def test_crumb_buffer(self):
        for enable in 1, 0:
            client = Client('http://foo:bar@example.com/0',
                            enable_breadcrumbs=enable)
            with client.context:
                breadcrumbs.record(type='foo', data={'bar': 'baz'},
                                   message='aha', category='huhu')
                crumbs = client.context.breadcrumbs.get_buffer()
                assert len(crumbs) == enable

    def test_log_crumb_reporting(self):
        client = Client('http://foo:bar@example.com/0')
        with client.context:
            log = logging.getLogger('whatever.foo')
            log.info('This is a message with %s!', 'foo', blah='baz')
            crumbs = client.context.breadcrumbs.get_buffer()

        assert len(crumbs) == 1
        assert crumbs[0]['type'] == 'default'
        assert crumbs[0]['category'] == 'whatever.foo'
        assert crumbs[0]['data'] == {'blah': 'baz'}
        assert crumbs[0]['message'] == 'This is a message with foo!'

    def test_log_crumb_reporting_with_dict(self):
        client = Client('http://foo:bar@example.com/0')
        with client.context:
            log = logging.getLogger('whatever.foo')
            log.info('This is a message with %(foo)s!', {'foo': 'bar'},
                     extra={'blah': 'baz'})
            crumbs = client.context.breadcrumbs.get_buffer()

        assert len(crumbs) == 1
        assert crumbs[0]['type'] == 'default'
        assert crumbs[0]['category'] == 'whatever.foo'
        assert crumbs[0]['data'] == {'foo': 'bar', 'blah': 'baz'}
        assert crumbs[0]['message'] == 'This is a message with bar!'

    def test_log_crumb_reporting_with_large_message(self):
        client = Client('http://foo:bar@example.com/0')
        with client.context:
            log = logging.getLogger('whatever.foo')
            log.info('a' * 4096)
            crumbs = client.context.breadcrumbs.get_buffer()

        assert len(crumbs) == 1
        assert crumbs[0]['message'] == 'a' * 1024

    def test_log_location(self):
        out = StringIO()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(out)
        handler.setFormatter(logging.Formatter(
            u'%(name)s|%(filename)s|%(funcName)s|%(lineno)d|'
            u'%(levelname)s|%(message)s'))
        logger.addHandler(handler)

        client = Client('http://foo:bar@example.com/0')
        with client.context:
            logger.info('Hello World!')
            lineno = sys._getframe().f_lineno - 1

        items = out.getvalue().strip().split('|')
        assert items[0] == 'tests.breadcrumbs.tests'
        assert items[1].rstrip('co') == 'tests.py'
        assert items[2] == 'test_log_location'
        assert int(items[3]) == lineno
        assert items[4] == 'INFO'
        assert items[5] == 'Hello World!'

    def test_broken_logging(self):
        client = Client('http://foo:bar@example.com/0')
        with client.context:
            log = logging.getLogger('whatever.foo')
            log.info('This is a message with %s. %s!', 42)
            crumbs = client.context.breadcrumbs.get_buffer()

        assert len(crumbs) == 1
        assert crumbs[0]['type'] == 'default'
        assert crumbs[0]['category'] == 'whatever.foo'
        assert crumbs[0]['message'] == 'This is a message with %s. %s!'

    def test_dedup_logging(self):
        client = Client('http://foo:bar@example.com/0')
        with client.context:
            log = logging.getLogger('whatever.foo')
            log.info('This is a message with %s!', 42)
            log.info('This is a message with %s!', 42)
            log.info('This is a message with %s!', 42)
            log.info('This is a message with %s!', 23)
            log.info('This is a message with %s!', 23)
            log.info('This is a message with %s!', 23)
            log.info('This is a message with %s!', 42)
            crumbs = client.context.breadcrumbs.get_buffer()

        assert len(crumbs) == 3
        assert crumbs[0]['type'] == 'default'
        assert crumbs[0]['category'] == 'whatever.foo'
        assert crumbs[0]['message'] == 'This is a message with 42!'
        assert crumbs[1]['type'] == 'default'
        assert crumbs[1]['category'] == 'whatever.foo'
        assert crumbs[1]['message'] == 'This is a message with 23!'
        assert crumbs[2]['type'] == 'default'
        assert crumbs[2]['category'] == 'whatever.foo'
        assert crumbs[2]['message'] == 'This is a message with 42!'

    def test_manual_record(self):
        client = Client('http://foo:bar@example.com/0')
        with client.context:
            def processor(data):
                assert data['message'] == 'whatever'
                assert data['level'] == 'warning'
                assert data['category'] == 'category'
                assert data['type'] == 'the_type'
                assert data['data'] == {'foo': 'bar'}
                data['data']['extra'] = 'something'

            breadcrumbs.record(message='whatever',
                               level='warning',
                               category='category',
                               data={'foo': 'bar'},
                               type='the_type',
                               processor=processor)

            crumbs = client.context.breadcrumbs.get_buffer()
            assert len(crumbs) == 1
            data = crumbs[0]
            assert data['message'] == 'whatever'
            assert data['level'] == 'warning'
            assert data['category'] == 'category'
            assert data['type'] == 'the_type'
            assert data['data'] == {'foo': 'bar', 'extra': 'something'}

    def test_special_log_handlers(self):
        name = __name__ + '.superspecial'
        logger = logging.getLogger(name)

        def handler(logger, level, msg, args, kwargs):
            assert logger.name == name
            assert msg == 'aha!'
            return True

        breadcrumbs.register_special_log_handler(name, handler)

        client = Client('http://foo:bar@example.com/0')
        with client.context:
            logger.debug('aha!')
            crumbs = client.context.breadcrumbs.get_buffer()
            assert len(crumbs) == 0

    def test_logging_handlers(self):
        name = __name__ + '.superspecial2'
        logger = logging.getLogger(name)

        def handler(logger, level, msg, args, kwargs):
            if logger.name == name:
                assert msg == 'aha!'
                return True

        breadcrumbs.register_logging_handler(handler)

        client = Client('http://foo:bar@example.com/0')
        with client.context:
            logger.debug('aha!')
            crumbs = client.context.breadcrumbs.get_buffer()
            assert len(crumbs) == 0

    def test_hook_libraries(self):

        @breadcrumbs.libraryhook('dummy')
        def _install_func():
            old_func = DummyClass.dummy_method

            def new_func(self):
                breadcrumbs.record(type='dummy', category='dummy', message="Dummy message")
                old_func(self)

            DummyClass.dummy_method = new_func

        client = Client('http://foo:bar@example.com/0', hook_libraries=['requests'])
        with client.context:
            DummyClass().dummy_method()
            crumbs = client.context.breadcrumbs.get_buffer()
            assert 'dummy' not in set([i['type'] for i in crumbs])

        client = Client('http://foo:bar@example.com/0', hook_libraries=['requests', 'dummy'])
        with client.context:
            DummyClass().dummy_method()
            crumbs = client.context.breadcrumbs.get_buffer()
            assert 'dummy' in set([i['type'] for i in crumbs])

