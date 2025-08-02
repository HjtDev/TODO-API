from django.db.models import QuerySet
from tag.models import Tag
from task.models import Task
from user.models import User
from rest_framework.test import APIClient
from authentication_tests import CONTENT_TYPE, VALID_PHONE
from django.urls import reverse
from tag.serializers import TagSerializer
import pytest, logging


logger = logging.getLogger(__name__)

TAG_URL = reverse('tag:tag-endpoints')
INVALID_NAME = 'invalid name' * 3

@pytest.fixture
def user():
    return User.objects.create_user(phone=VALID_PHONE)

@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def task(user) -> Task:
    return Task.objects.create(title='Task 1', user=user)

@pytest.fixture
def tags(task) -> QuerySet:
    tag1 = Tag.objects.create(name='Tag 1', user=task.user)
    tag2 = Tag.objects.create(name='Tag 2', user=task.user)
    tag3 = Tag.objects.create(name='Tag 3', user=task.user)
    tag1.tasks.add(task)
    tag2.tasks.add(task)
    tag3.tasks.add(task)
    return Tag.objects.all()

@pytest.mark.django_db
@pytest.mark.parametrize(
    'selector',
    ['', 'a', 'id1', 'task:a']
)
def test_invalid_parameter(client, selector):
    response = client.get(
        TAG_URL,
        data={
            'selector': selector,
        }
    )
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    'selector',
    ['5', 10, '100', 'task:10', 'task:100']
)
def test_get_not_found(client, selector):
    response = client.get(
        TAG_URL,
        data={
            'selector': selector,
        },
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_single_tags(client, tags):
    for tag in tags:
        response = client.get(
            TAG_URL,
            data={
                'selector': tag.id,
            }
        )
        assert response.status_code == 200

        data = response.json()

        assert 'tag' in data

        assert TagSerializer(instance=tag, data=data['tag']).is_valid(), 'Endpoint did not respond in a valid structure'


@pytest.mark.django_db
def test_get_task_tags(client, task, tags):

    response = client.get(
        TAG_URL,
        data={
            'selector': f'task:{task.id}',
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 'tags' in data
    assert len(data['tags']) == task.tags.count() == tags.count()

@pytest.mark.django_db
def test_get_all_tags(client, tags):
    response = client.get(
        TAG_URL,
        data={
            'selector': 'all'
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 'tags' in data
    assert len(data['tags']) == len(tags)

@pytest.mark.django_db
@pytest.mark.parametrize(
    'action,name,tag_id,task_id,expected',
    [
        ('', '', '', '', 400),
        ('haha', '', '', '', 400),
        ('create', '', '', '', 400),
        ('create', INVALID_NAME, '', '', 400),
        ('create', 'Tag', '', '', 201),
        ('create-connect', '', '', '1', 400),
        ('create-connect', 'Tag', '', '', 400),
        ('create-connect', 'Tag', '', 'bad_id', 400),
        ('create-connect', 'Tag', '', '100', 404),
        ('create-connect', 'Tag', '', '1', 201),
        ('connect', '', '', '1', 400),
        ('connect', '', '1', '', 400),
        ('connect', '', 'bad_id', '1', 400),
        ('connect', '', '1', 'bad_id', 400),
        ('connect', '', '1000', '1', 404),
        ('connect', '', '1', '404', 404),
        ('connect', '', '1', '1', 200),
        ('disconnect', '', '1', '1', 200)
    ]
)
def test_create_tag(client, tags, action, name, tag_id, task_id, expected):
    tag_task = tags.first().tasks.first()
    response = client.post(
        TAG_URL,
        data={
            'action': action,
            'name': name,
            'tag_id': tag_id if tag_id != '1' else tags.first().id,  # Here '1' means we need a valid ID so we replace it because the fixtures can't be called directly
            'task_id': task_id if task_id != '1' else tag_task.id
        },
        content_type=CONTENT_TYPE
    )
    logger.info(response.json())
    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'tag_id,name,expected',
    [
        ('', 'new_name', 400),
        ('1', '', 400),
        ('bad_id', 'new_name', 400),
        ('1000', 'new_name', 404),
        ('1', ' ', 400),
        ('1', INVALID_NAME, 400),
        ('1', 'new name', 200),
    ]
)
def test_edit_tag(client, tags, tag_id, name, expected):
    response = client.patch(
        TAG_URL,
        data={
            'tag_id': tag_id if tag_id != '1' else tags.first().id,
            'name': name
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == expected

    if expected == 200:
        data = response.json()
        assert 'tag' in data
        assert TagSerializer(instance=tags.first(), data=data['tag']).is_valid()

@pytest.mark.django_db
@pytest.mark.parametrize(
    'selector,expected',
    [
        ('', 400),
        ('bad_selector', 400),
        ('al', 400),
        ('10', 404),
        ('1', 200),
        (',', 404),
        ('10,20,30', 404),
        ('10,20,haha', 404),
        ('MULTIPLE_VALID_ID', 200),
        ('MULTIPLE_VALID_ID,20,30', 200),
        ('all', 200)
    ]
)
def test_delete_tag(client, tags, selector, expected):
    initial_count = tags.count()
    assert initial_count >= 3, 'This is test requires at least 3 tags'

    if selector == '1':
        final_selector = tags.first().id
    elif 'MULTIPLE_VALID_ID' in selector:
        final_selector = selector.replace('MULTIPLE_VALID_ID', ','.join(str(tag.id) for tag in tags))
    else:
        final_selector = selector

    response = client.delete(
        TAG_URL,
        data={
            'selector': final_selector,
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == expected
    count = tags.all().count()  # refresh and get the new count

    if expected != 200:
        return

    if selector.isdigit():
        assert initial_count - count == 1
    elif ',' in selector:
        assert initial_count - count <= len(selector.split(','))
    elif selector == 'all':
        assert count == 0
