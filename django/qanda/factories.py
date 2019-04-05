from django.conf import settings
from qanda.models import Question
from unittest.mock import patch
from user.factories import UserFactory

import factory

class QuestionFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Question {n}')
    question = 'What is a question?'
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Question

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        with patch('qanda.service.elasticsearch.Elasticsearch'):
            return super()._create(model_class, *args, **kwargs)