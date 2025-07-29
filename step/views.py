from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import status
from task.models import Task
from .models import Step
from .serializers import StepSerializer
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.permissions import IsAuthenticated
from user.views import AUTHENTICATION_REQUIRED, UNAUTHORIZED_RESPONSE, TOO_MANY_REQUESTS_RESPONSE
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse, OpenApiParameter
)


@extend_schema_view(
    get=extend_schema(
        tags=['Steps'],
        summary='Get Step(s)',
        description='Get Steps in 3 ways:\n\n1-Single step by STEP_ID\n\n2-Task steps by TASK_ID\n\n3-All steps related to authenticated user using "all" keyword' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='get',
                description='"STEP_ID" or "task:TASK_ID" or "all"',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Single step by STEP_ID',
                        value='1'
                    ),
                    OpenApiExample(
                        'Task steps by TASK_ID',
                        value='task:1'
                    ),
                    OpenApiExample(
                        'All steps',
                        value='all'
                    ),
                    OpenApiExample(
                        'Invalid parameter #1',
                        value='id1'
                    ),
                    OpenApiExample(
                        'Invalid parameter #2',
                        value='task:all'
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'get': {
                        'type': 'string',
                        'example': 'all',
                        'description': '"all" or "task:<TASK_ID>" or "<STEP_ID>"',
                    },
                },
                'required': ['get'],
                'examples': {
                    'Valid single step request': {
                        'value': {
                            'get': '1',
                        },
                        'description': 'Valid request'
                    },
                    'Valid task steps request': {
                        'value': {
                            'get': 'task:1',
                        },
                        'description': 'Valid request'
                    },
                    'Valid all steps request': {
                        'value': {
                            'get': 'all',
                        },
                        'description': 'Valid request'
                    }
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Success',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Valid single step response',
                        value={
                            'message': 'Success',
                            'step': {
                                'id': '<STEP_ID>',
                                'title': '<STEP_TITLE>',
                                'is_done': '<STEP_IS_DONE>',
                                'created_at': '<STEP_CREATED_AT>',
                                'updated_at': '<STEP_UPDATED_AT>',
                                'completed_at': '<STEP_COMPLETED_AT>',
                                'task': '<TASK_ID>',
                            }
                        }
                    ),
                    OpenApiExample(
                        'Valid task steps response',
                        value={
                            'message': 'Success',
                            'steps': [
                                {
                                    'id': '<STEP_ID>',
                                    'title': '<STEP_TITLE>',
                                    'is_done': '<STEP_IS_DONE>',
                                    'created_at': '<STEP_CREATED_AT>',
                                    'updated_at': '<STEP_UPDATED_AT>',
                                    'completed_at': '<STEP_COMPLETED_AT>',
                                    'task': '<TASK_ID>',
                                }
                            ]
                        }
                    ),
                    OpenApiExample(
                        'Valid all steps response',
                        value={
                            'message': 'Success',
                            'steps': [
                                {
                                    'id': '<STEP_ID>',
                                    'title': '<STEP_TITLE>',
                                    'is_done': '<STEP_IS_DONE>',
                                    'created_at': '<STEP_CREATED_AT>',
                                    'updated_at': '<STEP_UPDATED_AT>',
                                    'completed_at': '<STEP_COMPLETED_AT>',
                                    'task': '<TASK_ID>',
                                }
                            ]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Bad request',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No get parameter',
                        value={
                            'get': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid task id',
                        value={
                            'message': 'Invalid task id'
                        }
                    ),
                    OpenApiExample(
                        'Invalid get parameter',
                        value={
                            'message': 'Invalid get parameter'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Step/Task not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Step not found',
                        value={
                            'message': 'Step not found'
                        }
                    ),
                    OpenApiExample(
                        'Task not found',
                        value={
                            'message': 'Task not found'
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    )
)
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
