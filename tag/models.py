from django.db import models
from task.models import Task
from user.models import User


class Tag(models.Model):
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ('-created_at',)

    name = models.CharField('Name', max_length=30)

    tasks = models.ManyToManyField(Task, related_name='tags', blank=True, verbose_name='Tasks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags', verbose_name='User')

    created_at = models.DateTimeField('Created at', auto_now_add=True)
    updated_at = models.DateTimeField('Updated at', auto_now=True)

    def __str__(self):
        return self.name
