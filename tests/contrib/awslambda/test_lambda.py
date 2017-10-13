import pytest
from raven.transport.http import HTTPTransport


class MyException(Exception):
    pass


def test_decorator_exception(lambda_env, mock_client, lambda_event, lambda_context):

    client = mock_client()

    @client.capture_exceptions
    def test_func(event, context):
        raise MyException('There was an error.')

    with pytest.raises(MyException):
        test_func(event=lambda_event(), context=lambda_context(function_name='test_func'))

    assert client.events
    assert isinstance(client.remote.get_transport(), HTTPTransport)
    assert 'user' in client.events[0].keys()
    assert 'request' in client.events[0].keys()


def test_decorator_with_args(lambda_env, mock_client, lambda_event, lambda_context):
    client = mock_client()

    @client.capture_exceptions((MyException,))
    def test_func(event, context):
        raise Exception

    with pytest.raises(Exception):
        test_func(event=lambda_event(), context=lambda_context(function_name='test_func'))

    assert not client.events

    @client.capture_exceptions((MyException,))
    def test_func(event, context):
        raise MyException

    with pytest.raises(Exception):
        test_func(event=lambda_event(), context=lambda_context(function_name='test_func'))

    assert client.events


def test_decorator_without_exceptions(lambda_env, mock_client, lambda_event, lambda_context):
    client = mock_client()

    @client.capture_exceptions((MyException,))
    def test_func(event, context):
        return 0

    assert test_func(event=lambda_event(), context=lambda_context(function_name='test_func')) == 0


def test_decorator_without_kwargs(lambda_env, mock_client, lambda_event, lambda_context):

    client = mock_client()

    @client.capture_exceptions((MyException,))
    def test_func(event, context):
        raise MyException

    with pytest.raises(Exception):
        test_func(lambda_event(), lambda_context(function_name='test_func'))

    assert client.events
