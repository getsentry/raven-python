import sys
import logging

from raven.utils.testutils import TestCase

from raven.base import Client
from raven.breadcrumbs import record_breadcrumb

from io import StringIO


class BreadcrumbTestCase(TestCase):

    def test_crumb_buffer(self):
        for enable in 1, 0:
            client = Client('http://foo:bar@example.com/0',
                            enable_breadcrumbs=enable)
            with client.context:
                record_breadcrumb('foo', data={'bar': 'baz'},
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
