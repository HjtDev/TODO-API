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
    ),
    post=extend_schema(
        tags=['Steps'],
        summary='Create step',
        description='Create a step and connect it to a task' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='title',
                description='Step title. Must be less than 70 characters',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid step title',
                        value='Exersice for 30min'
                    ),
                    OpenApiExample(
                        'Invalid step title',
                        value='<TITLE: longer than 70 characters>'
                    )
                ]
            ),
            OpenApiParameter(
                name='task_id',
                description='The task\'s ID that is going to have this step',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid task id',
                        value='1'
                    )
                ]
            ),
            OpenApiParameter(
                name='is_done',
                description='To set the initial state of the step. Default: False',
                required=False,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Step is done',
                        value=True
                    ),
                    OpenApiExample(
                        'Step is not done',
                        value=False
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'task_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'Step will connect to this task',
                    },
                    'title': {
                        'type': 'string',
                        'example': 'Step 1',
                        'description': 'Step title',
                    },
                    'is_done': {
                        'type': 'boolean',
                        'example': False,
                        'description': 'Step initial state',
                    },
                },
                'required': ['task_id', 'title'],
                'examples': {
                    'Valid step request #1': {
                        'value': {
                            'task_id': '1',
                            'title': 'my step',
                        },
                        'description': 'Valid request without is_done'
                    },
                    'Valid step request #2': {
                        'value': {
                            'task_id': '1',
                            'title': 'my step',
                            'is_done': True,
                        },
                        'description': 'Valid request with is_done'
                    }
                }
            }
        },

        responses={
            201: OpenApiResponse(
                description='Step created successfully',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Success response',
                        value={
                            'message': 'Step created successfully',
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
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Bad request',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No title was provided',
                        value={
                            'title': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'No task_id was provided',
                        value={
                            'task_id': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid task_id parameter',
                        value={
                            'message': 'Invalid "task_id" parameter'
                        }
                    ),
                    OpenApiExample(
                        'Invalid field(title/is_done) value',
                        value={
                            '<FIELD>': ['FIELD_ERROR']
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Task not found',
                response=dict,
                examples=[
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
    ),
    patch=extend_schema(
        tags=['Steps'],
        summary='Edit step properties',
        description='Partially edit step properties' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='step_id',
                description='The ID of the step',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid step id',
                        value='1'
                    )
                ]
            ),
            OpenApiParameter(
                name='title',
                description='The new title of the step',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid title',
                        value='<TITLE: anything less than 70 characters>',
                    )
                ]
            ),
            OpenApiParameter(
                name='is_done',
                description='New state of the step',
                required=False,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Step is done',
                        value=True
                    ),
                    OpenApiExample(
                        'Step is not done',
                        value=False
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'step_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'ID of the step you need to edit',
                    },
                    'title': {
                        'type': 'string',
                        'example': 'Step 1',
                        'description': 'New step title',
                    },
                    'is_done': {
                        'type': 'boolean',
                        'example': False,
                        'description': 'new step state',
                    },
                },
                'required': ['step_id'],
                'examples': {
                    'Valid request': {
                        'value': {
                            'step_id': '1',
                            'title': 'new title',
                            'is_done': False,
                        },
                        'description': 'Changes the title and is_done status'
                    }
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Step updated successfully',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Success',
                        value={
                            'message': 'Step updated successfully',
                            'step': {
                                'id': '<STEP_ID>',
                                'title': '<NEW_STEP_TITLE>',
                                'is_done': '<NEW_STEP_IS_DONE>',
                                'created_at': '<STEP_CREATED_AT>',
                                'updated_at': '<STEP_UPDATED_AT>',
                                'completed_at': '<STEP_COMPLETED_AT>',
                                'task': '<TASK_ID>',
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Bad request',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No step_id was provided',
                        value={
                            'step_id': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid step_id parameter',
                        value={
                            'message': 'Invalid "step_id" parameter'
                        }
                    ),
                    OpenApiExample(
                        'Invalid field(title/is_done) value',
                        value={
                            '<FIELD>': ['FIELD_ERROR']
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Step not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Step not found',
                        value={
                            'message': 'Step not found'
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


    def post(self, request):
        try:
            data = self.get_data(request, 'title', 'task_id')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        task_id = data['task_id']
        if (isinstance(task_id, str) and task_id.isdigit()) or isinstance(task_id, int):
            try:
                task = request.user.tasks.get(id=task_id)
            except Task.DoesNotExist:
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )
        else:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message='Invalid "task_id" parameter'
            )

        serializer = StepSerializer(data=request.data)
        if not serializer.is_valid():
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **serializer.errors
            )

        serializer.save(task=task)

        return self.build_response(
            response_status=status.HTTP_201_CREATED,
            message='Step created successfully',
            step=serializer.data
        )

    def patch(self, request):
        try:
            step_id = self.get_data(request, 'step_id')['step_id']
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        if not self.is_id(step_id):
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message='Invalid "step_id" parameter'
            )

        try:
            step = Step.objects.get(id=step_id, task__user=request.user)
        except Step.DoesNotExist:
            return self.build_response(
                response_status=status.HTTP_404_NOT_FOUND,
                message='Step not found'
            )

        serializer = StepSerializer(instance=step, data=request.data, partial=True)

        if not serializer.is_valid():
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **serializer.errors
            )

        serializer.save()

        return self.build_response(
            response_status=status.HTTP_200_OK,
            message='Step updated successfully',
            step=serializer.data
        )

    def delete(self, request):
        try:
            selector = self.get_data(request, 'selector')['selector']
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        if self.is_id(selector):
            try:
                step = Step.objects.get(id=selector, task__user=request.user)
                step.delete()
                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message='Deleted 1 step successfully'
                )
            except Step.DoesNotExist:
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='Step not found'
                )

        if ',' in selector:
            ids = filter(None, selector.split(','))
            steps = Step.objects.filter(id__in=ids, task__user=request.user)
            if not steps.exists():
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='No steps found to delete'
                )
            to_delete = steps.count()
            steps.delete()
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message=f'Deleted {to_delete} step(s) successfully'
            )

        if 'task:' in selector:
            task_id = selector.split(':')[1]

            try:
                task = request.user.tasks.get(id=task_id)
                steps = task.steps.all()
                to_delete = steps.count()
                steps.delete()
                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message=f'Deleted {to_delete} step(s) successfully'
                )
            except Task.DoesNotExist:
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )

        if selector == 'all':
            steps = Step.objects.filter(task__user=request.user)
            to_delete = steps.count()
            steps.delete()
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message=f'Deleted all({to_delete}) step(s) successfully'
            )

        return self.build_response(
            response_status=status.HTTP_400_BAD_REQUEST,
            message='Invalid "selector" parameter'
        )
