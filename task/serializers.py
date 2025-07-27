from rest_framework.serializers import ModelSerializer, ReadOnlyField
from .models import Task


class NormalTaskSerializer(ModelSerializer):
    progress = ReadOnlyField()
    class Meta:
        model = Task
        fields = '__all__'


class QuickTaskSerializer(ModelSerializer):
    progress = ReadOnlyField()
    class Meta:
        model = Task
        fields = ('id', 'title', 'project', 'progress', 'is_done', 'is_archived', 'remind_at', 'due_at')
