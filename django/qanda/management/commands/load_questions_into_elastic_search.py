from django.core.management import BaseCommand

from qanda.service import elasticsearch
from qanda.models import Question

class Command(BaseCommand):
    help = 'Load all questions into Elasticsearch'

    def handle(self, *args, **kwargs):
        queryset = Question.objects.all()
        all_loaded = elasticsearch.bulk_load(queryset)
        if all_loaded:
            self.stdout.write(self.style.SUCCESS(
                'Successfully loaded all questions into ElasticSearch'
            ))
        else:
            self.stdout.write(
                self.style.WARNING(
                    'There were problems with one or more questions.'
                    'Check log files for additional information.'
                )
            )

