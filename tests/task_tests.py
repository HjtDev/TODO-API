from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from task.models import Task
from user.models import User
from django.urls import reverse
from django.conf import settings
from datetime import datetime
import pytest
import logging


logger = logging.getLogger(__name__)


VALID_PHONE = '0123456789'
REMIND_AT = timezone.now()
DUE_AT = timezone.now() + timedelta(days=1)
CONTENT_TYPE = 'application/json'

TASK_URL = reverse('task:task-endpoints')

@pytest.fixture
def user():
    return User.objects.create_user(phone=VALID_PHONE)

@pytest.fixture
def task(user):
    return Task.objects.create(
        user=user,
        title='Task 1',
        project='test',
        notes='Task notes',
        is_done=False,
        is_archived=False,
        remind_at=REMIND_AT,
        due_at=DUE_AT,
    )

@pytest.fixture
def tasks(user):
    Task.objects.create(
        user=user,
        title='Task 1',
        project='test',
        notes='Task notes',
        is_done=False,
        is_archived=False,
        remind_at=REMIND_AT,
        due_at=DUE_AT,
    )
    Task.objects.create(
        user=user,
        title='Task 2',
        project='test',
        notes='Task notes',
        is_done=False,
        is_archived=False,
        remind_at=REMIND_AT,
        due_at=DUE_AT,
    )
    return Task.objects.all()

@pytest.fixture
def client(db, user):
    client = APIClient()
    client.force_authenticate(user=user)
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['tasks'] = '1000/sec'
    return client


@pytest.mark.django_db
def test_get_single_task(client, task):
    # Test normal load
    response = client.get(
        TASK_URL,
        data={
            'get': task.id,
            'quick': False
        },
        content_type=CONTENT_TYPE,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'message' in data
    assert 'task' in data
    r_task = data['task']
    assert r_task['id'] == task.id
    assert r_task['progress'] == task.progress
    assert r_task['title'] == task.title
    assert r_task['project'] == task.project
    assert r_task['notes'] == task.notes
    assert r_task['is_done'] == task.is_done
    assert r_task['is_archived'] == task.is_archived
    assert r_task['remind_at'] == task.remind_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert r_task['due_at'] == task.due_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert 'created_at' in r_task
    assert 'updated_at' in r_task
    assert 'completed_at' in r_task
    assert r_task['user'] == task.user.id

    # Test quick load
    response = client.get(
        TASK_URL,
        data={
            'get': task.id,
            'quick': True
        },
        content_type=CONTENT_TYPE,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'message' in data
    assert 'task' in data
    r_task = data['task']
    assert r_task['id'] == task.id
    assert r_task['progress'] == task.progress
    assert r_task['title'] == task.title
    assert r_task['project'] == task.project
    assert r_task['is_done'] == task.is_done
    assert r_task['is_archived'] == task.is_archived
    assert r_task['remind_at'] == task.remind_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert r_task['due_at'] == task.due_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def test_get_all_tasks(client, tasks):
    # Quick load
    response = client.get(
        TASK_URL,
        data={
            'get': 'all',
            'quick': True
        },
        content_type=CONTENT_TYPE,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'message' in data
    assert 'tasks' in data
    r_data = data['tasks']

    assert isinstance(r_data, list)
    assert len(r_data) == tasks.count()


@pytest.mark.django_db
def test_task_creation(client):
    VALID_TITLE = 'Task title'
    INVALID_TITLE = 'Task Title' * 7

    # No title test
    response = client.post(
        TASK_URL,
        data={},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.json()

    # Invalid title test
    response = client.post(
        TASK_URL,
        data={
            'title': INVALID_TITLE,
        },
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert 'message' in data
    assert 'title' in data


    # Title only creation
    response = client.post(
        TASK_URL,
        data={
            'title': VALID_TITLE,
        },
        content_type=CONTENT_TYPE,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert 'message' in data
    assert 'task' in data

    task: dict = data['task']
    assert 'id' in task

    db_task = Task.objects.get(id=task['id'])

    assert VALID_TITLE == task['title'] == db_task.title
    assert task['project'] == db_task.project is None
    assert task['notes'] == db_task.notes is None
    assert task['is_done'] == db_task.is_done == False
    assert task['is_archived'] == db_task.is_archived == False
    assert task['remind_at'] == db_task.remind_at is None
    assert task['due_at'] == db_task.due_at is None

    # Full Task Creation Test
    response = client.post(
        TASK_URL,
        data={
            'title': VALID_TITLE,
            'project': 'test_project',
            'notes': 'test_notes',
            'is_done': True,
            'is_archived': True,
            'remind_at': '2025-07-28T09:00',
            'due_at': '2025-07-28T10:00',
        },
        content_type=CONTENT_TYPE,
    )
    logger.info(response.json())
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert 'message' in data
    assert 'task' in data

    task: dict = data['task']
    assert 'id' in task

    db_task = Task.objects.get(id=task['id'])

    assert VALID_TITLE == task['title'] == db_task.title
    assert task['project'] == db_task.project
    assert task['notes'] == db_task.notes
    assert task['is_done'] == db_task.is_done
    assert task['is_archived'] == db_task.is_archived

    assert datetime.strptime(task['remind_at'], '%Y-%m-%dT%H:%M:%SZ') == db_task.remind_at.replace(tzinfo=None)
    assert datetime.strptime(task['due_at'], '%Y-%m-%dT%H:%M:%SZ') == db_task.due_at.replace(tzinfo=None)
