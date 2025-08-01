from django.db import models
from user.models import User
from task.models import Task
from django.core.exceptions import ValidationError
import os


def profile_size_validator(value):
    # should be less than 3MB
    print(value.size)
    if value.size > 3145728:
        raise ValidationError('Profile picture must be less than 3MB.')


class Contact(models.Model):
    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ('-created_at',)

    name = models.CharField('Name', max_length=60)
    profile = models.ImageField('Profile Picture', upload_to='Profiles', default='default.png', validators=[profile_size_validator], blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts', verbose_name='User')
    tasks = models.ManyToManyField(Task, related_name='contacts', verbose_name='Task', blank=True)

    created_at = models.DateTimeField('Created at', auto_now_add=True)
    updated_at = models.DateTimeField('Updated at', auto_now=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.profile and self.profile.name != 'default.png':
            os.remove(self.profile.path)
        return super().delete(*args, **kwargs)
