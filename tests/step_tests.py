from step.models import Step
from task.models import Task
from rest_framework.test import APIClient
from tests.authentication_tests import CONTENT_TYPE
from user.models import User
from django.urls import reverse
from rest_framework import status
from step.serializers import StepSerializer
import pytest


STEPS_URL = reverse('step:step-endpoints')


@pytest.fixture
def user():
    return User.objects.create_user(phone='09123456789')


@pytest.fixture
def task(user):
    return Task.objects.create(title='Task 1', user=user)


@pytest.fixture
def step(task):
    return Step.objects.create(title='Step 1', task=task)


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_get_no_parameter(client):
    response = client.get(
        STEPS_URL,
        data={}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'get' in response.json()

@pytest.mark.django_db
@pytest.mark.parametrize(
    'parameter',
    [['al'], ['task-1'], ['1a'], 'abc']
)
def test_get_wrong_parameter(client, parameter):
    response = client.get(
        STEPS_URL,
        data={
            'get': parameter
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_does_not_exist(client):
    response = client.get(
        STEPS_URL,
        data={
            'get': '1'
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.get(
        STEPS_URL,
        data={
            'get': 'task:1'
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_single_step(client, step):

    response = client.get(
        STEPS_URL,
        data={
            'get': step.id
        }
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert 'step' in data

    serializer = StepSerializer(instance=step, data=data['step'])

    assert serializer.is_valid(), 'Endpoint did not return a valid response'


@pytest.mark.django_db
def test_get_task_steps(client, task, step):
    response = client.get(
        STEPS_URL,
        data={
            'get': f'task:{task.id}'
        }
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert 'steps' in data

    steps = data['steps']

    assert len(steps) == task.steps.count()

    serializer = StepSerializer(instance=task.steps.all(), data=steps, many=True)
    assert serializer.is_valid()


@pytest.mark.django_db
def test_get_all_steps(client, task):
    task_steps = task.steps.all()

    response = client.get(
        STEPS_URL,
        data={
            'get': 'all'
        }
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert 'steps' in data

    steps = data['steps']
    assert len(steps) == task_steps.count()

    for i in range(len(steps)):
        serializer = StepSerializer(data=steps[i])
        assert serializer.is_valid()
        assert serializer.instance in task_steps


@pytest.mark.django_db
def test_create_no_parameter(client):
    response = client.post(
        STEPS_URL,
        data={},
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(
        STEPS_URL,
        data={
            'title': 'Step 1'
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(
        STEPS_URL,
        data={
            'task_id': '1'
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_invalid_task_id(client):
    response = client.post(
        STEPS_URL,
        data={
            'title': 'Step 1',
            'task_id': 'task:1'
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(
        STEPS_URL,
        data={
            'title': 'Step 1',
            'task_id': '9999'
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_invalid_parameter(client, task):
    response = client.post(
        STEPS_URL,
        data={
            'title': 'Step 1' * 15,
            'task_id': task.id
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.json()


@pytest.mark.django_db
def test_create_step(client, task):
    response = client.post(
        STEPS_URL,
        data={
            'title': 'Step 1',
            'task_id': task.id
        }
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert 'step' in data

    data = data['step']

    assert 'id' in data

    assert Step.objects.filter(id=data['id']).exists(), 'Step was not created properly'

    assert task.steps.filter(id=data['id']).exists(), 'Step was not added to task properly'


@pytest.mark.django_db
def test_edit_no_parameter(client):
    response = client.patch(
        STEPS_URL,
        data={},
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'step_id' in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize(
    'step_id',
    ['id:1', 'a', -1, ' ', '-1']
)
def test_edit_invalid_parameter(client, step_id):
    response = client.patch(
        STEPS_URL,
        data={
            'step_id': step_id
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_edit_step_does_not_exist(client):
    response = client.patch(
        STEPS_URL,
        data={
            'step_id': '999'
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_edit_bad_parameter(client, step):
    response = client.patch(
        STEPS_URL,
        data={
            'step_id': step.id,
            'title': 'Step 1' * 15
        },
        content_type=CONTENT_TYPE
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.json()


@pytest.mark.django_db
def test_edit_step(client, step):
    response = client.patch(
        STEPS_URL,
        data={
            'step_id': step.id,
            'title': 'edited',
            'is_done': not step.is_done
        }
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert 'step' in data

    data = data['step']

    step.refresh_from_db()

    assert data == StepSerializer(instance=step).data, 'Invalid response from endpoint'
