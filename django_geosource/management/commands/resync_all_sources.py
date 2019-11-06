from django.core.management import BaseCommand

from django_geosource.models import Source


class Command(BaseCommand):
    help = "Launch resync of all sources availables"

    def add_arguments(self, parser):
        parser.add_argument("--force", dest="force", action="store_true")

    def handle(self, *args, **options):
        for source in Source.objects.all():
            source.run_async_method("refresh_data", force=options["force"])
