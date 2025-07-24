from datetime import timedelta

from django.core.cache import cache
from django.conf import settings
from random import randint
from typing import Dict, Any
from django.core.exceptions import ImproperlyConfigured


class OTP:
    def __init__(self, indicator: str, config: Dict[str, Any] = None):
        self.indicator = indicator
        self.encoder = settings.CIPHER

        self.settings = getattr(settings, 'OTP_SETTINGS', {}).copy()
        if config:
            self.settings.update(config)
        if not self.settings:
            raise ImproperlyConfigured('OTP_SETTINGS is not configured')

        self.expiration_time = None

        self.validate_settings()

    def validate_settings(self):
        try:  # DIGITS Validation
            digits = self.settings['DIGITS']
            if not isinstance(digits, int):
                raise TypeError('OTP_SETTINGS["DIGITS"] must be an int')
            if digits < 2:
                raise ValueError('OTP_SETTINGS["DIGITS"] must be at least 2')
        except KeyError as e:
            raise KeyError('OTP_SETTINGS["DIGITS"] must be defined')

        try:
            expiration_time = self.settings['EXPIRATION_TIME']

            if not isinstance(expiration_time, timedelta):
                raise TypeError('OTP_SETTINGS["EXPIRATION_TIME"] must be an instance of timedelta')

            self.expiration_time = expiration_time.total_seconds()
            if self.expiration_time < 1:
                raise ValueError('OTP_SETTINGS["EXPIRATION_TIME"] must be greater than 0 seconds')
        except KeyError as e:
            raise KeyError('OTP_SETTINGS["EXPIRATION_TIME"] must be defined')

    def generate_token(self) -> str:
        start = 10 ** (self.settings['DIGITS'] - 1)
        end = (10 ** self.settings['DIGITS']) - 1

        return str(randint(int(start), int(end)))

    def save_token(self, token: str, **kwargs) -> bool:
        if len(token) != self.settings['DIGITS']:
            return False
        if cache.get(f'{self.indicator}-otp'):
            return False
        encoded_token = self.encoder.encrypt(token.encode())
        kwargs.update({'token': encoded_token})
        cache.set(f'{self.indicator}-otp', kwargs, self.expiration_time)
        return True

    def restore_token(self) -> (bool, str, dict):
        data: dict | None = cache.get(f'{self.indicator}-otp')

        if data is None:
            return False, 'NO_ACTIVE_OTP', dict()

        if not isinstance(data, dict):
            return False, 'OTP_MISMATCH', dict()

        token = data.pop('token', None)

        if token is None:
            return False, 'NO_TOKEN_FOUND', data

        return True, token, data

    def validate_otp(self, token: str) -> (bool, str | dict):
        success, result, extra = self.restore_token()

        if not success:
            return success, result
        # noinspection PyBroadException
        try:
            decrypted_token = self.encoder.decrypt(result).decode()
        except Exception as e:
            return False, 'FAILED TO DECRYPT OTP'

        return decrypted_token == token, extra

    def cancel_otp(self) -> bool:
        return cache.delete(f'{self.indicator}-otp')

    def __str__(self):
        return f'OTP - {self.indicator}'
