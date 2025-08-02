from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from .models import Step


@receiver(pre_save, sender=Step)
def step_completed_at(sender, instance: Step, **kwargs):
    if not instance.pk and instance.completed_at:
        instance.completed_at = timezone.now()

    if instance.pk and not Step.objects.get(pk=instance.pk).is_done and instance.is_done:
        instance.completed_at = timezone.now()