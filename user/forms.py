from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
import re


phone_pattern = re.compile(r'^09\d{9}$')
email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_phone(number):
    return bool(phone_pattern.match(number))


def validate_email(email):
    return bool(email_pattern.match(email))


class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone', 'name', 'is_active', 'is_staff', 'is_superuser')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if self.instance.pk:
            if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Phone already exists.')
        else:
            if User.objects.filter(phone=phone).exists():
                raise forms.ValidationError('Phone already exists.')

        if not phone.isdigit():
            raise forms.ValidationError('phone must be a number.')

        if not phone.startswith('09'):
            raise forms.ValidationError('phone must start with 09 digits.')

        if len(phone) != 11:
            raise forms.ValidationError('phone must have 11 digits.')

        return phone


class UserChangeFormNew(UserChangeForm):
    class Meta:
        model = User
        fields = ('phone', 'name', 'is_active', 'is_staff', 'is_superuser')
