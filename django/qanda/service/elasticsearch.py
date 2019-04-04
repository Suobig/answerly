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
    client = get_client()
    bulk = streaming_bulk(
        client,
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

def search_for_questions(query):
    client = get_client()
    result = client.search(
        index=settings.ES_INDEX,
        body={
            'query': {
                'match': {
                    'text': query,
                },
            },
        },
    )
    logger.info(f"Elasticsearch returned {result['hits']['total']} results for query '{query}'"
                f"Query took {result['took']}ms")
    return (h['_source'] for h in result['hits']['hits'])

def upsert(question):
    client = get_client()
    question_dict = question.as_elasticsearch_dict()
    doc_type = question_dict['_type']
    del question_dict['_id']
    del question_dict['_type']
    response = client.update(
        index=settings.ES_INDEX,
        doc_type=doc_type,
        id=question.id,
        body={
            'doc': question_dict,
            'doc_as_upsert': True,
        }
    )
    return response