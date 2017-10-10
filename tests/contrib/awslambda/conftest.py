
import pytest
from raven.contrib.awslambda import LambdaClient
import uuid
import time


class MockClient(LambdaClient):
    def __init__(self, *args, **kwargs):
        self.events = []
        super(MockClient, self).__init__(*args, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)

    def is_enabled(self, **kwargs):
        return True


class LambdaIndentityStub(object):
    def __init__(self, id=1, pool_id=1):
        self.cognito_identity_id = id
        self.cognito_identity_pool_id = pool_id

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, name, default=None):
        return getattr(self, name, default)


class LambdaContextStub(object):

    def __init__(self, function_name, memory_limit_in_mb=128, timeout=300, function_version='$LATEST'):
        self.function_name = function_name
        self.memory_limit_in_mb = memory_limit_in_mb
        self.timeout = timeout
        self.function_version = function_version
        self.timeout = timeout
        self.invoked_function_arn = 'invoked_function_arn'
        self.log_group_name = 'log_group_name'
        self.log_stream_name = 'log_stream_name'
        self.identity = LambdaIndentityStub(id=0, pool_id=0)
        self.client_context = None
        self.aws_request_id = str(uuid.uuid4())
        self.start_time = time.time() * 1000

    def __getitem__(self, item, default):
        return getattr(self, item, default)

    def get(self, name, default=None):
        return getattr(self, name, default)

    def get_remaining_time_in_millis(self):
        return max(self.timeout * 1000 - int((time.time() * 1000) - self.start_time), 0)


class LambdaEventStub(object):
    def __init__(self, body=None, headers=None, http_method='GET', path='/test', query_string=None):
        self.body = body
        self.headers = headers
        self.httpMethod = http_method
        self.isBase64Encoded = False
        self.path = path
        self.queryStringParameters = query_string
        self.resource = path
        self.stageVariables = None
        self.requestContext = {
            'accountId': '0000000',
            'apiId': 'AAAAAAAA',
            'httpMethod': http_method,
            'identity': LambdaIndentityStub(),
            'path': path,
            'requestId': 'test-request',
            'resourceId': 'bbzeyv',
            'resourcePath': '/test',
            'stage': 'test-stage'
        }

    def __getitem__(self, name):
        return getattr(self, name)

    def get(self, name, default=None):
        return getattr(self, name, default)


@pytest.fixture
def lambda_env(monkeypatch):
    monkeypatch.setenv('SENTRY_DSN', 'http://public:secret@example.com/1')
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME', 'test_func')
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_VERSION', '$LATEST')
    monkeypatch.setenv('SENTRY_RELEASE', '$LATEST')
    monkeypatch.setenv('SENTRY_ENVIRONMENT', 'testing')


@pytest.fixture
def mock_client():
    return MockClient

@pytest.fixture
def lambda_event():
    return LambdaEventStub

@pytest.fixture
def lambda_context():
    return LambdaContextStub
