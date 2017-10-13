Amazon Web Services Lambda
==========================

.. default-domain:: py



Installation
------------

To use `Sentry`_ with `AWS Lambda`_, you have to install `raven` as an external
dependency. This involves creating a `Deployment package`_ and uploading it
to AWS.

To install raven into your current project directory:

.. code-block:: console

    pip install raven -t /path/to/project-dir

Setup
-----

Create a `LambdaClient` instance and wrap your lambda handler with
the `capture_exeptions` decorator:


.. sourcecode:: python

    from raven.contrib.awslambda import LambdaClient


    client = LambdaClient()

    @client.capture_exceptions
    def handler(event, context):
        ...
        raise Exception('I will be sent to sentry!')


By default this will report unhandled exceptions and errors to Sentry.

Additional settings for the client are configured using environment variables or
subclassing `LambdaClient`.


The integration was inspired by `raven python lambda`_, another implementation that
also integrates with Serverless Framework and has SQS transport support. 


.. _Sentry: https://getsentry.com/
.. _AWS Lambda: https://aws.amazon.com/lambda
.. _Deployment package: https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
.. _raven python lambda: https://github.com/Netflix-Skunkworks/raven-python-lambda
