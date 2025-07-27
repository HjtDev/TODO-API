from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from .serializers import NormalTaskSerializer, QuickTaskSerializer
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
