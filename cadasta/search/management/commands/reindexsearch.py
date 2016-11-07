from django.core.management.base import BaseCommand

from ... import reindex


class Command(BaseCommand):
    help = "Repopulate the search indexes."

    def handle(self, *args, **options):
        reindex.run()
