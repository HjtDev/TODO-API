from rest_framework.serializers import ModelSerializer
from .models import Step


class StepSerializer(ModelSerializer):
    class Meta:
        model = Step
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'id', 'task', 'completed_at')
