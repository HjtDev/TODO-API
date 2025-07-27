from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from task.models import Task
from user.models import User
from django.urls import reverse
import pytest
from django.conf import settings
import json


VALID_PHONE = '0123456789'
REMIND_AT = timezone.now()
DUE_AT = timezone.now() + timedelta(days=1)
TASK_URL = reverse('task:task-endpoints')
CONTENT_TYPE = 'application/json'

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

