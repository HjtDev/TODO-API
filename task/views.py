from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from .serializers import NormalTaskSerializer, QuickTaskSerializer, CreateTaskSerializer
from .models import Task
from user.models import User
from rest_framework.views import APIView
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from user.views import AUTHENTICATION_REQUIRED, UNAUTHORIZED_RESPONSE, TOO_MANY_REQUESTS_RESPONSE
import logging


logger = logging.getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        tags=['Tasks'],
        summary='Get task(s)',
        description='You can get a list of your tasks or a single one by id' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='get',
                description='"all" or "<ID>"',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'All Tasks',
                        value='all'
                    ),
                    OpenApiExample(
                        'Single Task',
                        value='<ID>'
                    )
                ]
            ),
            OpenApiParameter(
                name='quick',
                description='If set to ("true", "True", "1", 1, "y", "yes") only shows essential fields of task in response',
                required=True,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Normal',
                        value=False
                    ),
                    OpenApiExample(
                        'Quick',
                        value=True
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
                        'description': '"all" or "<ID>"'
                    },
                    'quick': {
                        'type': 'boolean',
                        'example': 'true',
                        'description': 'Anything other than ("true", "True", "1", 1, "y", "yes") is considered as false'
                    }
                },
                'required': ['get', 'quick'],
                'examples': {
                    'Valid Request': {
                        'value': {
                            'get': '2',
                            'quick': 'false'
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
                        'Success Response for all Tasks with quick load',
                        value={
                            'message': 'Success',
                            'tasks': [
                                {
                                    "id": 2,
                                    "title": "Task 2",
                                    "project": "final",
                                    "progress": 0,
                                    "is_done": True,
                                    "is_archived": False,
                                    "remind_at": "2025-07-27T17:00:00Z",
                                    "due_at": "2025-07-30T10:00:00Z"
                                },
                                {
                                    "id": 1,
                                    "title": "First Task",
                                    "project": "initial",
                                    "progress": 0,
                                    "is_done": False,
                                    "is_archived": True,
                                    "remind_at": "2025-07-28T09:00:00Z",
                                    "due_at": None
                                }
                            ]
                        }
                    ),
                    OpenApiExample(
                        'Success Response for single Task with normal load',
                        value={
                            'message': 'Success',
                            'task': {
                                "id": 1,
                                "progress": 0,
                                "title": "First Task",
                                "project": "initial",
                                "notes": "some notes",
                                "is_done": False,
                                "is_archived": True,
                                "remind_at": "2025-07-28T09:00:00Z",
                                "due_at": None,
                                "created_at": "2025-07-27T16:13:29.643186Z",
                                "updated_at": "2025-07-27T16:25:39.473721Z",
                                "completed_at": None,
                                "user": 1
                            }
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    ),
    post=extend_schema(
        tags=['Tasks'],
        summary='Task Creation',
        description='Quick create a task with title or create a full task with all fields',

        parameters=[
            OpenApiParameter(
                name='title',
                description='Task title',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Title',
                        value='Test Task'
                    ),
                    OpenApiExample(
                        'Invalid Title',
                        value='<TITLE: longer than 50 characters>'
                    )
                ]
            ),
            OpenApiParameter(
                name='project',
                description='Task scope',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Project',
                        value='House Chores'
                    )
                ]
            ),
            OpenApiParameter(
                name='notes',
                description='Task notes',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Notes',
                        value='Call Mickael too!'
                    )
                ]
            ),
            OpenApiParameter(
                name='is_done',
                description='Task completion status',
                required=False,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Task Not Completed',
                        value=False
                    ),
                    OpenApiExample(
                        'Task Completed',
                        value=True
                    )
                ]
            ),
            OpenApiParameter(
                name='is_archived',
                description='Used for archived tasks',
                required=False,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Task Archived',
                        value=True
                    ),
                    OpenApiExample(
                        'Task Not Archived',
                        value=False
                    )
                ]
            ),
            OpenApiParameter(
                name='remind_at',
                description='Task reminder date/time. Format: YYYY-MM-DDTHH:MM:SS',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Task Reminder',
                        value='2025-07-28T09:00:00'
                    )
                ]
            ),
            OpenApiParameter(
                name='due_at',
                description='Task due date/time. Format: YYYY-MM-DDTHH:MM:SS',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Task Due Date',
                        value='2025-07-28T09:45:00'
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'title': {
                        'type': 'string',
                        'example': 'Test Task',
                        'description': 'Task title'
                    },
                    'project': {
                        'type': 'string',
                        'example': 'House Chores',
                        'description': 'Task project'
                    },
                    'notes': {
                        'type': 'string',
                        'example': 'Call Mickael too!',
                        'description': 'Task notes'
                    },
                    'is_done': {
                        'type': 'boolean',
                        'example': False,
                        'description': 'Task completion status'
                    },
                    'is_archived': {
                        'type': 'boolean',
                        'example': False,
                        'description': 'Task archived status'
                    },
                    'remind_at': {
                        'type': 'string',
                        'example': '2025-07-28T09:00:00',
                        'description': 'Task reminder date/time'
                    },
                    'due_at': {
                        'type': 'string',
                        'example': '2025-07-28T09:45:00',
                        'description': 'Task due date/time'
                    }
                },
                'required': ['title'],
                'examples': {
                    'Title only request': {
                        'value': {
                            'title': 'test title',
                        },
                        'description': 'Title only request'
                    },
                    'Full request': {
                        'value': {
                            'title': 'task 2',
                            'project': 'project 2',
                            'notes': 'a lot of notes',
                            'is_done': False,
                            'is_archived': True,
                            'remind_at': '2025-07-27T16:15:00',
                            'due_at': '2025-07-27T17:30:00'
                        }
                    }
                }
            }
        },

        responses={
            201: OpenApiResponse(
                description='Task Created Successfully',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Task Created Successful',
                        value={
                            'message': 'Task created',
                            'task': {
                                'id': 1,
                                'title': '<TITLE>',
                                'project': '<PROJECT>',
                                'notes': '<NOTES>',
                                'is_done': '<IS_DONE>',
                                'is_archived': '<IS_ARCHIVED>',
                                'remind_at': '<REMIND_AT>',
                                'due_at': '<DUE_AT>',
                                'completed_at': '<COMPLETED_AT>'
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Failed to create task',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No title was provided',
                        value={
                            'title': 'this field is required',
                        }
                    ),
                    OpenApiExample(
                        'Invalid title',
                        value={
                            'message': 'Failed to create task',
                            'title': ['<ERROR1>', '<ERROR2>']
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    ),
    patch=extend_schema(
        tags=['Tasks'],
        summary='Task partial update',
        description='Change task fields(same as task creation fields).',

        parameters=[
            OpenApiParameter(
                name='task_id',
                description='Task ID',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Task ID',
                        value='1'
                    ),
                    OpenApiExample(
                        'Invalid Task ID',
                        value='a'
                    )
                ],
            ),
            OpenApiParameter(
                name='title',
                description='Task title',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Title',
                        value='Test Task'
                    ),
                    OpenApiExample(
                        'Invalid Title',
                        value='<TITLE: longer than 50 characters>'
                    )
                ]
            ),
            OpenApiParameter(
                name='project',
                description='Task scope',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Project',
                        value='House Chores'
                    )
                ]
            ),
            OpenApiParameter(
                name='notes',
                description='Task notes',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Valid Notes',
                        value='Call Mickael too!'
                    )
                ]
            ),
            OpenApiParameter(
                name='is_done',
                description='Task completion status',
                required=False,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Task Not Completed',
                        value=False
                    ),
                    OpenApiExample(
                        'Task Completed',
                        value=True
                    )
                ]
            ),
            OpenApiParameter(
                name='is_archived',
                description='Used for archived tasks',
                required=False,
                type=bool,
                examples=[
                    OpenApiExample(
                        'Task Archived',
                        value=True
                    ),
                    OpenApiExample(
                        'Task Not Archived',
                        value=False
                    )
                ]
            ),
            OpenApiParameter(
                name='remind_at',
                description='Task reminder date/time. Format: YYYY-MM-DDTHH:MM:SS',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Task Reminder',
                        value='2025-07-28T09:00:00'
                    )
                ]
            ),
            OpenApiParameter(
                name='due_at',
                description='Task due date/time. Format: YYYY-MM-DDTHH:MM:SS',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Task Due Date',
                        value='2025-07-28T09:45:00'
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
                        'description': 'Task ID'
                    },
                    'title': {
                        'type': 'string',
                        'example': 'Test Task',
                        'description': 'Task title'
                    },
                    'project': {
                        'type': 'string',
                        'example': 'House Chores',
                        'description': 'Task project'
                    },
                    'notes': {
                        'type': 'string',
                        'example': 'Call Mickael too!',
                        'description': 'Task notes'
                    },
                    'is_done': {
                        'type': 'boolean',
                        'example': False,
                        'description': 'Task completion status'
                    },
                    'is_archived': {
                        'type': 'boolean',
                        'example': False,
                        'description': 'Task archived status'
                    },
                    'remind_at': {
                        'type': 'string',
                        'example': '2025-07-28T09:00:00',
                        'description': 'Task reminder date/time'
                    },
                    'due_at': {
                        'type': 'string',
                        'example': '2025-07-28T09:45:00',
                        'description': 'Task due date/time'
                    }
                },
                'required': ['task_id'],
                'examples': {
                    'Full update': {
                        'value': {
                            'task_id': '1',
                            'title': 'updated title',
                            'project': 'updated project',
                            'notes': 'updated notes',
                            'is_done': True,
                            'is_archived': False,
                            'remind_at': '2025-07-27T16:00:00',
                            'due_at': '2025-07-27T17:00:00'
                        }
                    }
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Task updated successfully',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Task updated successfully',
                        value={
                            'message': 'Task updated',
                            'task': {
                                'id': '<TASK_ID>',
                                'title': '<TITLE>',
                                'project': '<PROJECT>',
                                'notes': '<NOTES>',
                                'is_done': '<IS_DONE>',
                                'is_archived': '<IS_ARCHIVED>',
                                'remind_at': '<REMIND_AT>',
                                'due_at': '<DUE_AT>',
                                'completed_at': '<COMPLETED_AT>'
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Failed to update task',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No task_id was provided',
                        value={
                            'task_id': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Bad field value',
                        value={
                            'message': 'Failed to update task',
                            '<FIELD>': ['FIELD_ERRORS']
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
    )
)
class TaskView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tasks'

    def get(self, request):
        try:
            data = self.get_data(request, 'get', 'quick')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail,
            )

        if data['get'] != 'all' and not data['get'].isdigit():
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message='Invalid "get" parameter ("all" or "task_id")',
            )

        serializer = QuickTaskSerializer if self.convert_data_to_bool(data['quick']) else NormalTaskSerializer

        if data['get'] == 'all':
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message='Success',
                tasks=serializer(request.user.tasks.all(), many=True).data,
            )

        try:
            task = request.user.tasks.get(id=data['get'])
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message='Success',
                task=serializer(task).data,
            )
        except Task.DoesNotExist:
            return self.build_response(
                response_status=status.HTTP_404_NOT_FOUND,
                message='Task not found',
            )

    def post(self, request):
        try:
            data = self.get_data(request, 'title')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail,
            )

        serializer = CreateTaskSerializer(data=request.data)

        if serializer.is_valid():
            task = serializer.save(user=request.user)
            return self.build_response(
                response_status=status.HTTP_201_CREATED,
                message='Task created',
                task=serializer.data
            )

        return self.build_response(
            response_status=status.HTTP_400_BAD_REQUEST,
            message='Failed to create task',
            **serializer.errors,
        )

    def patch(self, request):
        try:
            data = self.get_data(request, 'task_id')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail,
            )

        try:
            task = request.user.tasks.get(id=data['task_id'])
            serializer = CreateTaskSerializer(instance=task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message='Task updated',
                    task=serializer.data
                )
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message='Failed to update task',
                **serializer.errors,
            )
        except Task.DoesNotExist:
            return self.build_response(
                response_status=status.HTTP_404_NOT_FOUND,
                message='Task not found',
            )

    def delete(self, request):
        try:
            data = self.get_data(request, 'task_id')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                **e.detail,
            )

        if (isinstance(data['task_id'], str) and data['task_id'].isdigit()) or isinstance(data['task_id'], int):
            try:
                task = request.user.tasks.get(id=data['task_id'])
                task.delete()
                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message=f'Deleted 1 task successfully',
                )
            except Task.DoesNotExist:
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='Task not found',
                )

        if ',' in data['task_id']:
            ids = filter(None, data['task_id'].split(','))
            tasks = request.user.tasks.filter(id__in=ids)
            if not tasks.exists():
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='No task found to delete',
                )
            to_delete_count = tasks.count()
            tasks.delete()
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message=f'Deleted {to_delete_count} tasks successfully',
            )

        if data['task_id'] == 'all':
            tasks = request.user.tasks.all()
            if not tasks.exists():
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='There is no task to delete',
                )
            task_count = tasks.count()
            tasks.delete()
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message=f'Deleted all({task_count}) tasks successfully',
            )

        return self.build_response(
            response_status=status.HTTP_400_BAD_REQUEST,
            message='Invalid task_id parameter',
        )
