import threading
from raven.utils.testutils import TestCase

from raven.base import Client
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

    def test_thread_binding(self):
        client = Client()
        called = []

        class TestContext(Context):

            def activate(self):
                Context.activate(self)
                called.append('activate')

            def deactivate(self):
                called.append('deactivate')
                Context.deactivate(self)

        # The main thread activates the context but clear does not
        # deactivate.
        context = TestContext(client)
        context.clear()
        assert called == ['activate']

        # But another thread does.
        del called[:]

        def test_thread():
            # This activate is unnecessary as the first activate happens
            # automatically
            context.activate()
            context.clear()
        t = threading.Thread(target=test_thread)
        t.start()
        t.join()
        assert called == ['activate', 'activate', 'deactivate']
