from __future__ import absolute_import

from raven.utils.transaction import TransactionStack


def test_simple():
    stack = TransactionStack()

    stack.push('foo')

    assert len(stack) == 1
    assert stack.peek() == 'foo'

    bar = stack.push(['bar'])

    assert len(stack) == 2
    assert stack.peek() == ['bar']

    stack.push({'baz': True})

    assert len(stack) == 3
    assert stack.peek() == {'baz': True}

    stack.pop(bar)

    assert len(stack) == 1
    assert stack.peek() == 'foo'

    stack.pop()

    assert len(stack) == 0
    assert stack.peek() == None


def test_context_manager():
    stack = TransactionStack()

    with stack('foo'):
        assert stack.peek() == 'foo'

    assert stack.peek() is None
