from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from random import choice
import os


class UserManager(BaseUserManager):

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Users must have a phone number')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)


def profile_directory_path(instance, filename):
    return os.path.join(
        'Profiles',
        f'user_{instance.id}',
        filename
    )

def phone_validator(value):
    if not value.isdigit():
        raise ValidationError('Phone number must only contain numbers.')

    if not value.startswith('09'):
        raise ValidationError('Phone number must start with 09.')

    if len(value) != 11:
        raise ValidationError('Phone number must contain 11 digits.')

    return value

class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=11, unique=True, verbose_name='Phone number', validators=[phone_validator])
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email')
    name = models.CharField(max_length=60, verbose_name='Name', blank=True, null=True)
    profile = models.ImageField(upload_to=profile_directory_path, default='default.png', verbose_name='Profile', help_text='64*64', blank=True, null=True)

    is_active = models.BooleanField(default=True, verbose_name='Access')
    is_staff = models.BooleanField(default=False, verbose_name='Is Staff')
    is_superuser = models.BooleanField(default=False, verbose_name='Is Owner')

    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Registration date')

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.name or self.phone

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
