import sys
import logging

from raven.utils.testutils import TestCase

from raven.base import Client
from raven.breadcrumbs import record_breadcrumb

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


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
        out = BytesIO()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(out)
        handler.setFormatter(logging.Formatter(
            '%(name)s|%(filename)s|%(funcName)s|%(lineno)d|'
            '%(levelname)s|%(message)s'))
        logger.addHandler(handler)

        client = Client('http://foo:bar@example.com/0')
        with client.context:
            logger.info('Hello World!')
            lineno = sys._getframe().f_lineno - 1

        items = out.getvalue().strip().decode('utf-8').split('|')
        assert items[0] == b'tests.breadcrumbs.tests'
        assert items[1].rstrip(b'co') == b'tests.py'
        assert items[2] == b'test_log_location'
        assert int(items[3]) == lineno
        assert items[4] == b'INFO'
        assert items[5] == b'Hello World!'
