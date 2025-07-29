from django.db import models
from task.models import Task


class Step(models.Model):
    class Meta:
        verbose_name = 'Step'
        verbose_name_plural = 'Steps'
        ordering = ('-created_at',)
        indexes = [
            models.Index(
                fields=['-created_at'],
            )
        ]
    title = models.CharField('Title', max_length=70)
    is_done = models.BooleanField('Is done', default=False)

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='steps', verbose_name='Task')

    created_at = models.DateTimeField('Created at', auto_now_add=True)
    updated_at = models.DateTimeField('Updated at', auto_now=True)
    completed_at = models.DateTimeField('Completed at', null=True, blank=True)

    def __str__(self):
        return f'<Step: {self.title}>'
