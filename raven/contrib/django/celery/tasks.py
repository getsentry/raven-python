# TODO: need to educate myself on how this works

from raven.contrib.django.models import get_client

# We just need to pull in the client to ensure the task is registered
client = get_client()