from rest_framework.serializers import ModelSerializer
from .models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone', 'email', 'name', 'profile', 'date_joined', 'is_active', 'is_staff', 'is_superuser')
        read_only_fields = ('id', 'phone', 'date_joined', 'is_active', 'is_staff', 'is_superuser')
