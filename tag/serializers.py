from rest_framework.serializers import ModelSerializer
from .models import Tag


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ('id', 'tasks', 'user', 'created_at', 'updated_at')