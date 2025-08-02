from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from task.models import Task


@receiver(pre_save, sender=Task)
def task_completed_at(sender, instance: Task, **kwargs):
    if not instance.pk and instance.is_done:
        instance.completed_at = timezone.now()

    if instance.pk and not Task.objects.get(pk=instance.pk).is_done and instance.is_done:
        instance.completed_at = timezone.now()

