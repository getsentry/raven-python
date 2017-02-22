from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Examples'

    def handle(self, *args, **options):
        raise Exception('oops')
