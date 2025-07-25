from time import sleep
from django.core.cache import cache
from django.conf import settings
import pytest


INDICATOR = 'test_encryption'
CIPHER = settings.CIPHER

@pytest.mark.parametrize(
    'data,expected',
    [
        ('1234', '1234'),
        ('abcd', 'abcd'),
        ('A1b2', 'A1b2'),
        ('G!1w', 'G!1w'),
    ]
)
def test_encryption(data, expected):
    encrypted_data = CIPHER.encrypt(data.encode())

    cache.set(INDICATOR, encrypted_data)

    sleep(.1)

    data = cache.get(INDICATOR)

    assert data == encrypted_data

    decrypted_data = CIPHER.decrypt(encrypted_data).decode()

    assert decrypted_data == expected
