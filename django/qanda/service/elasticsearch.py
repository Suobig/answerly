import logging

from django.conf import settings
from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import streaming_bulk

#__name__ is a special variable that shows:
# - if module is being run directly: '__main__'
# - if module is being imported: name of the module that imported it
logger = logging.getLogger(__name__)

def get_client():
    return Elasticsearch(hosts=[
        {
            'host': settings.ES_HOST,
            'port': settings.ES_PORT,
        }
    ])

def bulk_load(questions):
    all_ok = True
    es_questions = (q.as_elasticsearch_dict() for q in questions)
    bulk = streaming_bulk(
        get_client(),
        es_questions,
        index = settings.ES_INDEX,
        raise_on_error=False,
    )
    for ok, result in bulk:
        if not ok:
            all_ok = False
            action, result = result.popitem()
            logger.error(f"Failed to load {result['id']}: {result!r}")
    return all_ok