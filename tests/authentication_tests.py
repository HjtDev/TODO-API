from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from user.models import User
from user.otp import OTP
from django.conf import settings
from PIL import Image
import pytest, tempfile, os


VALID_PHONE = '09123456789'
INVALID_PHONE = '9123456789'
CONTENT_TYPE = 'application/json'
START_AUTH_URL = reverse('user:start-authentication')
COMPLETE_AUTH_URL = reverse('user:complete-authentication')
TOKEN_RENEW_URL = reverse('user:renew-token')
EDIT_PROFILE_URL = reverse('user:edit-profile')

@pytest.fixture
def client(db):
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth'] = '1000/sec'
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth_verify'] = '1000/sec'
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth_renew'] = '1000/sec'
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


@pytest.mark.django_db
def test_complete_authentication(client):
    # No data
    response = client.post(
        COMPLETE_AUTH_URL,
        data={},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Phone only
    response = client.post(
        COMPLETE_AUTH_URL,
        data={'phone': VALID_PHONE},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Token only
    response = client.post(
        COMPLETE_AUTH_URL,
        data={'token': '1234'},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Invalid phone
    response = client.post(
        COMPLETE_AUTH_URL,
        data={
            'phone': INVALID_PHONE,
            'token': '1234'
        },
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # No Active OTP
    response = client.post(
        COMPLETE_AUTH_URL,
        data={
            'phone': VALID_PHONE,
            'token': '1234'
        },
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test Valid OTP request
    response = client.post(
        START_AUTH_URL,
        data={'phone': VALID_PHONE},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'cooldown' in response.json()

    # Test Invalid Token
    response = client.post(
        COMPLETE_AUTH_URL,
        data={
            'phone': VALID_PHONE,
            'token': '1234'
        },
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


    # Test Valid Token
    otp = OTP(VALID_PHONE)
    success, encrypted_token, extra = otp.restore_token()
    assert success
    decrypted = otp.encoder.decrypt(encrypted_token).decode()

    response = client.post(
        COMPLETE_AUTH_URL,
        data={
            'phone': VALID_PHONE,
            'token': decrypted
        },
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert 'user' in response_data
    assert 'auth' in response_data
    assert 'refresh' in response_data['auth']
    assert 'access' in response_data['auth']
    assert 'refresh_expires_in' in response_data['auth']
    assert 'access_expires_in' in response_data['auth']

    otp.cancel_otp()


@pytest.mark.django_db
def test_token_renewal(client):
    response = client.post(
        START_AUTH_URL,
        data={'phone': VALID_PHONE},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK

    otp = OTP(VALID_PHONE)
    success, encrypted_token, extra = otp.restore_token()
    decrypted = otp.encoder.decrypt(encrypted_token).decode()

    response = client.post(
        COMPLETE_AUTH_URL,
        data={
            'phone': VALID_PHONE,
            'token': decrypted
        },
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    refresh = data['auth']['refresh']

    assert RefreshToken(refresh)
    refresh = RefreshToken(refresh)

    # Test no refresh token
    response = client.post(
        COMPLETE_AUTH_URL,
        data={},
        content_type=CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test Invalid refresh token
    response = client.post(
        TOKEN_RENEW_URL,
        data={'refresh': 'abcd'},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Test valid token
    response = client.post(
        TOKEN_RENEW_URL,
        data={'refresh': refresh.token},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'auth' in data
    assert 'access' in data['auth']
    assert 'access_expires_in' in data['auth']

    # Test Blacklisted token
    refresh.blacklist()

    response = client.post(
        TOKEN_RENEW_URL,
        data={'refresh': refresh.token},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Test expired refresh token
    user, _ = User.objects.get_or_create(phone=VALID_PHONE)
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=-timedelta(days=1))
    response = client.post(
        TOKEN_RENEW_URL,
        data={'refresh': str(refresh)},
        content_type=CONTENT_TYPE,
    )
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_edit_profile(client):
    # Create a test image dynamically
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        Image.new('RGB', (100, 100)).save(tmp_file, 'PNG')
        tmp_file_path = tmp_file.name

    try:
        user = User.objects.create_user(
            phone=VALID_PHONE,
            email='test@gmail.com',
            name='test user'
        )

        client.force_authenticate(user=user)

        with open(tmp_file_path, 'rb') as img:
            response = client.patch(
                EDIT_PROFILE_URL,
                data={
                    'email': 'new@gmail.com',
                    'name': 'new name',
                    'profile': img
                },
                format='multipart'  # Important for file uploads
            )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()

        assert user.email == 'new@gmail.com'
        assert user.name == 'new name'
        assert user.profile.name != ''  # Check file was saved
        assert os.path.exists(user.profile.path)  # Verify file exists on filesystem

    finally:
        # Cleanup
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        if hasattr(user, 'profile') and user.profile:
            user.profile.delete()