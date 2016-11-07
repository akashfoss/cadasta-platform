from django.core.management.base import BaseCommand

from ... import reindex


class Command(BaseCommand):
    help = "Repopulate the search index of a project."

    def add_arguments(self, parser):
        parser.add_argument('project', type=str)

    def handle(self, *args, **options):
        project_slug = options['project']
        reindex.run(project_slug)
