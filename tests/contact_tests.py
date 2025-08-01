from encodings.punycode import selective_len

from contact.models import Contact
from contact.serializers import ContactSerializer
from authentication_tests import CONTENT_TYPE
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from task.models import Task
import pytest, logging
from user.models import User

logger = logging.getLogger(__name__)
CONTACT_URL = reverse('contact:contact-endpoints')
INVALID_NAME = '1234567890' * 7

@pytest.fixture
def user():
    return User.objects.create_user(phone='09123456789')

@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def task(user):
    return Task.objects.create(title='Task 1', user=user)

@pytest.fixture
def contact(user, task):
    contact =  Contact.objects.create(name='Test Contact', user=user)
    contact.tasks.add(task)
    return contact

@pytest.fixture
def contacts(user, task):
    Contact.objects.create(name='Contact 1', user=user).tasks.add(task)
    Contact.objects.create(name='Contact 2', user=user).tasks.add(task)
    Contact.objects.create(name='Contact 3', user=user).tasks.add(task)
    return Contact.objects.all()

@pytest.fixture
def tasks(user, contact):
    Task.objects.create(title='Task 1', user=user).contacts.add(contact)
    Task.objects.create(title='Task 2', user=user).contacts.add(contact)
    Task.objects.create(title='Task 3', user=user).contacts.add(contact)
    return Task.objects.all()

def get_actual_selector(selector: str, contact, contacts, task) -> str:
    if selector == 'C_VALID':
        return str(contact.id)

    elif selector == 'CM_VALID':
        return ','.join(str(contact_id) for contact_id in contacts.values_list('id', flat=True))

    elif selector == 'T_VALID':
        return f'task:{task.id}'

    elif selector == 'TS_VALID':
        return str(task.id)

    else:
        return selector

@pytest.mark.django_db
@pytest.mark.parametrize(
    'selector,expected',
    [
        ('', 400),
        ('bad_selector', 400),
        ('1000', 404),
        ('C_VALID', 200),
        (',', 404),
        (',,,', 404),
        ('10,20,30', 404),
        ('10,20,a', 404),
        ('10,20,', 404),
        ('10,,c', 404),
        ('CM_VALID', 200),
        ('task:', 400),
        ('task:a', 400),
        ('task:all', 400),
        ('task:1000', 404),
        ('T_VALID', 200),
        ('all', 200)
    ]
)
def test_get_contacts(client, contact, contacts, task, selector, expected):
    response = client.get(
        CONTACT_URL,
        data={
            'selector': get_actual_selector(selector, contact, contacts, task),
        }
    )
    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'action,name,contact_id,task_id,expected',
    [
        ('', '', '', '', 400),
        (' ', '', '', '', 400),
        ('hhaa', '', '', '', 400),
        ('create', '', '', '', 400),
        ('create', ' ', '', '', 400),
        ('create', INVALID_NAME, '', '', 400),
        ('create', 'Test', '', '', 201),
        ('connect', '', '1', '', 400),
        ('connect', '', '', '1', 400),
        ('connect', '', '1', '1', 404),
        ('connect', '', 'C_VALID', '1', 404),
        ('connect', '', '1', 'TS_VALID', 404),
        ('connect', '', 'C_VALID', 'TS_VALID', 200),
        ('disconnect', '', '1', '', 400),
        ('disconnect', '', '', '1', 400),
        ('disconnect', '', '1', '1', 404),
        ('disconnect', '', 'C_VALID', '1', 404),
        ('disconnect', '', '1', 'TS_VALID', 404),
        ('disconnect', '', 'C_VALID', 'TS_VALID', 200),
    ]
)
def test_create_contact(client, contact, contacts, task, action, name, contact_id, task_id, expected):
    response = client.post(
        CONTACT_URL,
        data={
            'action': action,
            'name': name,
            'contact_id': get_actual_selector(contact_id, contact, contacts, task),
            'task_id':  get_actual_selector(task_id, contact, contacts, task)
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == expected

@pytest.mark.django_db
@pytest.mark.parametrize(
    'contact_id,name, expected',
    [
        ('', '', 400),
        (' ', '', 400),
        ('a', '', 400),
        ('id1', '', 400),
        ('1000', '', 404),
        ('C_VALID', '', 400),
        ('C_VALID', ' ', 400),
        ('C_VALID', INVALID_NAME, 400),
        ('C_VALID', 'Test Name', 200)
    ]
)
def test_patch_contact(client, contact, contact_id, name, expected):
    response = client.patch(
        CONTACT_URL,
        data={
            'contact_id': get_actual_selector(contact_id, contact, None, None),
            'name': name
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == expected

@pytest.mark.django_db
@pytest.mark.parametrize(
    'selector,expected',
    [
        ('', 400),
        (' ', 400),
        ('al', 400),
        ('1', 404),
        ('C_VALID', 200),
        (',', 404),
        (',,', 404),
        ('a,b,c', 404),
        ('a,b,10', 404),
        ('10,20,30', 404),
        ('CM_VALID', 200),
        ('all', 200)
    ]
)
def test_delete_contact(client, contact, contacts, selector, expected):
    initial_count = Contact.objects.count()
    response = client.delete(
        CONTACT_URL,
        data={
            'selector': get_actual_selector(selector, contact, contacts, None),
        },
        content_type=CONTENT_TYPE
    )
    assert response.status_code == expected
    if expected == 200:
        assert initial_count - Contact.objects.count() >= 1
