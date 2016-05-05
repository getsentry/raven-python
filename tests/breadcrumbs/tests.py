import logging

from raven.utils.testutils import TestCase

from raven.base import Client
from raven.breadcrumbs import record_breadcrumb


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
