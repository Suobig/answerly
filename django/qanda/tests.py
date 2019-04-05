from datetime import date

from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.conf import settings

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from elasticsearch import Elasticsearch
from selenium.webdriver.chrome.webdriver import WebDriver

from qanda.models import Question
from qanda.factories import QuestionFactory
from qanda.views import DailyQuestionList
from user.factories import UserFactory



QUESTION_CREATED_STRFTIME = '%Y-%m-%d %H:%M'
SUCCESS_CODE = 200

class QuestionSaveTestCase(TestCase):
    """
    Tests Question.save()
    """

    @patch('qanda.service.elasticsearch.Elasticsearch')
    def test_elasticsearch_upsert_on_save(self, ElasticsearchMock):

        q = QuestionFactory()
        q.save()

        #Check that question was added to DB
        self.assertIsNotNone(q.id)
        #Check that our mock service was called
        self.assertTrue(ElasticsearchMock.called)
        mock_client = ElasticsearchMock.return_value
        #Test that we called service with expected parameters
        mock_client.update.assert_called_once_with(
            index=settings.ES_INDEX,
            doc_type='doc',
            id=q.id,
            body={
                'doc': {
                    'text': f'{q.title}\n{q.question}',
                    'question_body': q.question,
                    'title': q.title,
                    'id': q.id,
                    'created': q.created,
                },
                'doc_as_upsert': True,
            },
        )

class DailyQuestionListTestCase(TestCase):
    """
    Test the DailyQuestionList view
    """
    #Path won't be used for rooting, so we can pass whatever
    REQUEST = RequestFactory().get(path='/q/2013-11-12')
    TODAY = date.today()
    QUESTION_COUNT = 10

    def test_GET_on_day_with_many_questions(self):
        todays_questions = [
            QuestionFactory() for _ in range(self.QUESTION_COUNT)
        ]

        response = DailyQuestionList.as_view()(
            self.REQUEST,
            year=self.TODAY.year,
            month=self.TODAY.month,
            day=self.TODAY.day,
        )

        self.assertEqual(
            SUCCESS_CODE, 
            response.status_code,
        )
        self.assertEqual(
            self.QUESTION_COUNT, 
            response.context_data['object_list'].count()
        )
        rendered_content = response.rendered_content
        # print(rendered_content)
        for question in todays_questions:
            created = question.created.strftime(
                QUESTION_CREATED_STRFTIME
            )
            needle = f'''
                <li>
                    <a href="/q/{question.id}">{question.title}</a>
                    by {question.user.username} on {created}
                </li>
            '''
            self.assertInHTML(needle, rendered_content)

class QuestionDetailViewTestCase(TestCase):
    """
    Integration testing for QuestionDetailView
    """
    NO_ANSWERS_NEEDLE = '''
    <li class="answer">No answers yet!</li>
    '''
    NOT_LOGGED_NEEDLE = '<div>Login to post answers.</div>'

    def test_logged_in_user_can_post_answers(self):
        question = QuestionFactory()

        self.assertTrue(self.client.login(
            username=question.user.username,
            password=UserFactory.password,
        ))

        response = self.client.get(f'/q/{question.id}')
        self.assertEqual(SUCCESS_CODE, response.status_code)

        content = response.rendered_content
        self.assertInHTML(self.NO_ANSWERS_NEEDLE, content)

        template_names = [t.name for t in response.templates]
        self.assertIn("qanda/common/post_answer.html", template_names)
        # print(content)

        created = question.created.strftime(QUESTION_CREATED_STRFTIME)
        needle = f'''
            <div class="question">
                <div class="meta col-sm-12">
                    <h1>{question.title}</h1>
                    Asked by {question.user.username} 
                    on {created}
                </div>
                <div class="body col-sm-12">
                    <p>{question.question}</p>
                </div>
            </div>
        '''
        self.assertInHTML(needle, content)

    def test_not_logged_user_cant_post_answers(self):
        question = QuestionFactory()

        response = self.client.get(f'/q/{question.id}')
        self.assertEqual(SUCCESS_CODE, response.status_code)
        #Not logged user shouldn't see post_answer template
        template_names = [t.name for t in response.templates]
        self.assertNotIn("qanda/common/post_answer.html", template_names)
        #He should see a message instead.
        content = response.rendered_content
        self.assertInHTML(self.NOT_LOGGED_NEEDLE, content)


class AskQuestionTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver(executable_path=settings.CHROMEDRIVER)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = UserFactory()


    def test_cant_ask_blank_question(self):
        """
        Live test ask question form using selenium
        """
        initial_question_count = Question.objects.count()

        self.selenium.get(f'{self.live_server_url}/user/login')
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.user.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys(UserFactory.password)
        #Login to the app
        self.selenium.find_element_by_id('login').click()

        #Go to ask question view
        self.selenium.find_element_by_link_text("Ask").click()
        
        initial_url = self.selenium.current_url
        #Try to submit an empty question
        ask_button = self.selenium.find_element_by_id("ask")
        ask_button.click()
        self.check_submission_failed(initial_url, initial_question_count)

        #Try enter only title
        title_input = self.selenium.find_element_by_name("title")
        title_input.send_keys("Test")
        ask_button.click()
        self.check_submission_failed(initial_url, initial_question_count)

        #Now try enter only question
        title_input.clear()
        body_input = self.selenium.find_element_by_name("question")
        body_input.send_keys("Test")
        self.check_submission_failed(initial_url, initial_question_count)
        #Logout
        self.selenium.find_element_by_link_text("Logout").click()


    def check_submission_failed(self, init_url, init_count):
        """
        Check that submission attempt failed 
        (stayed on the same page & no new questions were created)
        """
        current_url = self.selenium.current_url
        self.assertEqual(init_url, current_url)
        current_question_count = Question.objects.count()
        self.assertEqual(init_count, current_question_count)
