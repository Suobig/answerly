import datetime

from qanda.models import (
    Answer,
    Question,
)
from django.contrib.auth.models import User
from django.utils import timezone
from random import choice

from bs4 import BeautifulSoup
from urllib import parse, request


def top_questions():
    base_url = 'https://stackoverflow.com/'
    url = 'https://stackoverflow.com/?tab=featured'
    html = request.urlopen(url)
    soup = BeautifulSoup(html, features='html.parser')
    questions = soup.find_all('a', {'class': 'question-hyperlink'})
    
    for question in questions[:100]:
        question_url = parse.urljoin(base_url, question.get('href'))
        yield question_url
        
users = User.objects.all()

def get_user():
    return choice(users)

def get_question_date(url):
    question = Question()
    html = request.urlopen(url)
    soup = BeautifulSoup(html, features='html.parser')
    title = soup.find('a', {'class': 'question-hyperlink'}).contents[0]
    try:
        text = soup.find('div', {'class': 'post-text'}).contents[1]
    except IndexError:
        text = ''
    dt = soup.find('span', {'class': 'relativetime'}).get('title')
    dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%SZ')
    dt = datetime.datetime(
            dt.year, 
            dt.month, 
            dt.day, 
            dt.hour, 
            dt.minute, 
            dt.second, 
            tzinfo=timezone.utc
        )

    question.title = title
    question.question = text.__str__
    question.user = get_user()
    question.created = dt

    return question
        
def load_questions():
    for url in top_questions():
        try:
            question = get_question_date(url)
        except Exception:
            print('Failed to load ' + url)
        else:
            # print(question.__repr__)
            print(f'Saving {question.title}...', end=' ')
            question.save()
            print('OK')