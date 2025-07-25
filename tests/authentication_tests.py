import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user.models import User
from user.otp import OTP
from django.conf import settings


VALID_PHONE = '09123456789'
INVALID_PHONE = '9123456789'
CONTENT_TYPE = 'application/json'
START_AUTH_URL = reverse('user:start-authentication')

@pytest.fixture
def client(db):
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth'] = '1000/sec'
    yield APIClient()


@pytest.mark.django_db
def test_valid_authentication(client):
    # Cancel any existing OTP
    OTP(VALID_PHONE).cancel_otp()

    # Test initial OTP request
    response = client.post(
        START_AUTH_URL,
        data={'phone': VALID_PHONE},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'cooldown' in response.json()

    # Test duplicate OTP prevention
    response = client.post(
        START_AUTH_URL,
        data={'phone': VALID_PHONE},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_423_LOCKED

    # Clear for other tests
    assert OTP(VALID_PHONE).cancel_otp()

@pytest.mark.django_db
def test_invalid_authentication(client):
    # Test missing phone
    response = client.post(
        START_AUTH_URL,
        data={},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test invalid format
    response = client.post(
        START_AUTH_URL,
        data={'phone': INVALID_PHONE},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST