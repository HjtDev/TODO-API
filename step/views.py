from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import status

from task.models import Task
from .models import Step
from .serializers import StepSerializer
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.permissions import IsAuthenticated


class StepView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'steps'

    def get(self, request):
        try:
            get = self.get_data(request, 'get')['get']
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        if (isinstance(get, str) and get.isdigit()) or isinstance(get, int):
            try:
                step = Step.objects.get(id=get, task__user=request.user)
                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message='Success',
                    step=StepSerializer(step).data,
                )
            except Step.DoesNotExist:
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='Step not found'
                )

        if 'task:' in get:
            task_id = get.split(':')[1]

            if not task_id.isdigit():
                return self.build_response(
                    response_status=status.HTTP_400_BAD_REQUEST,
                    message='Invalid task ID'
                )

            try:
                task = request.user.tasks.get(id=task_id)
                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message='Success',
                    steps=StepSerializer(task.steps.all(), many=True).data,
                )
            except Task.DoesNotExist:
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )

        if get == 'all':
            steps = Step.objects.filter(task__user=request.user)
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message='Success',
                steps=StepSerializer(steps, many=True).data
            )

        return self.build_response(
            response_status=status.HTTP_400_BAD_REQUEST,
            message='Invalid "get" parameter'
        )
