from time import sleep

from user.otp import OTP
from django.core.cache import cache
from datetime import timedelta
import pytest


@pytest.fixture
def otp(request):
    # Create unique indicator for each test
    indicator = f"test_{request.node.name[:30]}"
    # Clear before test
    cache.delete(f'{indicator}-otp')
    # Create OTP instance with test config
    yield OTP(
        indicator,
    )
    # Clear after test
    cache.delete(f'{indicator}-otp')

@pytest.mark.parametrize(
    'digits,expected_length',
    [(2, 2), (4, 4), (6, 6)],
    ids=['2-digits', '4-digits', '6-digits']
)
def test_token_generation(otp, digits, expected_length):
    # Temporarily modify digits for this test
    otp.settings['DIGITS'] = digits
    token = otp.generate_token()

    assert isinstance(token, str)
    assert token.isdigit()
    assert len(token) == expected_length
    # Verify numeric range
    assert 10**(expected_length-1) <= int(token) <= 10**expected_length - 1

def test_save_token(otp):
    token = otp.generate_token()

    # Test initial save
    assert otp.save_token(token), "Failed to save initial token"

    # Verify cache contents using the same indicator the fixture uses
    saved_data = cache.get(f'{otp.indicator}-otp')
    assert saved_data is not None, "Data not saved to cache"
    assert 'token' in saved_data, "Token not stored in cache data"

    # Verify encryption
    decrypted = otp.encoder.decrypt(saved_data['token']).decode()
    assert decrypted == token, "Encryption/decryption mismatch"

    # Test duplicate prevention
    assert not otp.save_token(otp.generate_token()), "Should prevent new token when one exists"

def test_restore_token(otp):
    # No active OTP scenario
    success, result, extra = otp.restore_token()
    assert not success
    assert result == 'NO_ACTIVE_OTP'
    assert extra == {}

    # Invalid format scenario
    cache.set(f'{otp.indicator}-otp', 'invalid_data')
    success, result, extra = otp.restore_token()
    assert not success
    assert result == 'OTP_MISMATCH'
    assert extra == {}

    # No token scenario
    cache.set(f'{otp.indicator}-otp', {'valid': 'data'})
    success, result, extra = otp.restore_token()
    assert not success
    assert result == 'NO_TOKEN_FOUND'
    assert extra == {'valid': 'data'}
    cache.delete(f'{otp.indicator}-otp')

    # Successful scenario
    test_data = {'meta': 'data'}
    token = otp.generate_token()
    assert otp.save_token(token, **test_data)

    success, encrypted_token, extra = otp.restore_token()
    assert success
    decrypted = otp.encoder.decrypt(encrypted_token).decode()
    assert decrypted == token
    assert extra == test_data


def test_validate_otp(otp):
    token = otp.generate_token()
    test_data = {'meta': 'data'}
    assert otp.save_token(token, **test_data), 'Failed to save initial token'

    # Invalid token
    success, extra = otp.validate_otp('1234')
    assert not success
    assert extra == 'INVALID_OTP_TOKEN'

    # Success
    success, extra = otp.validate_otp(token)
    assert success
    assert extra == test_data

    cache.delete(f'{otp.indicator}-otp')

    # No Token
    success, extra = otp.validate_otp(token)
    assert not success
    assert extra == 'NO_ACTIVE_OTP'


def test_cancel_otp(otp):
    assert otp.save_token(otp.generate_token()), 'Failed to save initial token'

    assert cache.get(f'{otp.indicator}-otp') is not None, 'Cache backend failed'

    assert otp.cancel_otp(), 'Failed to cancel OTP'

    assert cache.get(f'{otp.indicator}-otp') is None, 'Failed to remove OTP data'

    assert not otp.cancel_otp(), 'Should fail when no OTP exists'


def test_otp_expire(otp):
    otp.expiration_time = 3
    token = otp.generate_token()
    test_data = {'meta': 'data'}

    # Success
    assert otp.save_token(token, **test_data), 'Failed to save initial token'
    sleep(1)
    success, result = otp.validate_otp(token)
    assert success, 'Failed to validate OTP in time'
    assert result == test_data, 'Failed to retrieve extra data'

    assert otp.cancel_otp(), 'Failed to finish OTP validation'

    # Fail
    assert otp.save_token(token, **test_data), 'Failed to save token'
    sleep(3.1)
    success, result = otp.validate_otp(token)
    assert not success, 'Should fail when passes the expiration time'
    assert result == 'NO_ACTIVE_OTP'


