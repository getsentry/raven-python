from raven.utils.testutils import TestCase

from raven.context import Context


class ContextTest(TestCase):
    def test_simple(self):
        context = Context()
        context.merge({'foo': 'bar'})
        context.merge({'biz': 'baz'})
        context.merge({'biz': 'boz'})
        assert context.get() == {
            'foo': 'bar',
            'biz': 'boz',
        }

    def test_tags(self):
        context = Context()
        context.merge({'tags': {'foo': 'bar'}})
        context.merge({'tags': {'biz': 'baz'}})
        assert context.get() == {
            'tags': {
                'foo': 'bar',
                'biz': 'baz',
            }
        }

    def test_extra(self):
        context = Context()
        context.merge({'extra': {'foo': 'bar'}})
        context.merge({'extra': {'biz': 'baz'}})
        assert context.get() == {
            'extra': {
                'foo': 'bar',
                'biz': 'baz',
            }
        }
