from django.db import models
from user.models import User


class Task(models.Model):
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-completed_at']),
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')

    title = models.CharField('Title', max_length=50)
    project = models.CharField('Project', max_length=50, blank=True, null=True)
    notes = models.TextField('Notes', blank=True, null=True)

    is_done = models.BooleanField('Is done', default=False)
    is_archived = models.BooleanField('Is archived', default=False)

    created_at = models.DateTimeField('Created at', auto_now_add=True)
    updated_at = models.DateTimeField('Updated at', auto_now=True)
    completed_at = models.DateTimeField('Completed at')

    @property
    def progress(self):
        return 0  # temporary

    def __str__(self):
        return self.title
