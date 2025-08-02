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


class CreateTaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'project', 'notes', 'is_done', 'is_archived', 'remind_at', 'due_at', 'completed_at')
        read_only_fields = ('id',)
        extra_kwargs = {'id': {'read_only': True}, 'completed_at': {'read_only': True}}
