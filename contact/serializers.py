from .models import Contact
from rest_framework.serializers import ModelSerializer


class ContactSerializer(ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ('id', 'user', 'tasks', 'created_at', 'updated_at')
