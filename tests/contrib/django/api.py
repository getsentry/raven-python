from __future__ import absolute_import

from uuid import uuid4
from tastypie.bundle import Bundle
from tastypie.resources import Resource

from raven.contrib.django.models import client


class Item(object):
    def __init__(self, pk=None, name=None):
        self.pk = pk or uuid4().hex
        self.name = name or ''


class ExampleResource(Resource):
    class Meta:
        resource_name = 'example'
        object_class = Item

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.pk
        else:
            kwargs['pk'] = bundle_or_obj.pk

        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        try:
            raise Exception('oops')
        except:
            client.captureException()
        return []

    def obj_create(self, bundle, **kwargs):
        try:
            raise Exception('oops')
        except:
            client.captureException()

        bundle.obj = Item(**kwargs)
        bundle = self.full_hydrate(bundle)
        return bundle

    def obj_update(self, bundle, **kwargs):
        return self.obj_create(bundle, **kwargs)


class AnotherExampleResource(Resource):
    class Meta:
        resource_name = 'another'
        object_class = Item

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.pk
        else:
            kwargs['pk'] = bundle_or_obj.pk

        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        try:
            raise Exception('oops')
        except:
            client.captureException()
        return []

    def obj_create(self, bundle, **kwargs):
        try:
            raise Exception('oops')
        except:
            client.captureException()

        bundle.obj = Item(**kwargs)
        bundle = self.full_hydrate(bundle)
        return bundle

    def obj_update(self, bundle, **kwargs):
        return self.obj_create(bundle, **kwargs)
