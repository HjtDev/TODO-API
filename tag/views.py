from rest_framework.views import APIView
from task.models import Task
from .serializers import TagSerializer
from .models import Tag
from rest_framework import status
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from user.views import AUTHENTICATION_REQUIRED, UNAUTHORIZED_RESPONSE, TOO_MANY_REQUESTS_RESPONSE
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, OpenApiParameter
)


@extend_schema_view(
    get=extend_schema(
        tags=['Tags'],
        summary='Get tag(s)',
        description='Get tags in 3 modes:\n\n1-Single tag by ID\n\n2-All the tags connected to a task\n\n3-All the tags connected to authenticated user' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='selector',
                description='Selects tag(s) to retrieve',
                type=str,
                required=True,
                examples=[
                    OpenApiExample(
                        'Single tag: <TAG_ID>',
                        value='1'
                    ),
                    OpenApiExample(
                        'Task tags: task:<TASK_ID>',
                        value='task:1'
                    ),
                    OpenApiExample(
                        'All tags: all',
                        value='all'
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'selector': {
                        'type': 'string',
                        'example': '1',
                        'description': 'Tags to retrieve',
                    }
                },
                'required': ['selector'],
                'examples': {
                    'Valid single tag request': {
                        'value': {
                            'selector': '1'
                        },
                        'description': 'Retrieves the tag with ID 1 if it exists'
                    },
                    'Valid task tags request': {
                        'value': {
                            'selector': 'task:1'
                        },
                        'description': 'Retrieves task with ID 1 tags, if it exists'
                    },
                    'Valid all tags request': {
                        'value': {
                            'selector': 'all'
                        },
                        'description': 'Retrieves all tags connected to the authenticated user'
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
                        'Single tag response',
                        value={
                            'message': 'Success',
                            'tag': {
                                'id': '<TAG_ID>',
                                'name': '<TAG_NAME>',
                                'created_at': '<TAG_CREATED_AT>',
                                'updated_at': '<TAG_UPDATED_AT>',
                                'user': '<AUTHENTICATED_USER_ID>',
                                'tasks': [
                                    '<TASK_ID>',
                                ]
                            }
                        }
                    ),
                    OpenApiExample(
                        'Task tag response',
                        value={
                            'message': 'Success',
                            'tags': [
                                {
                                    'id': '<TAG_ID>',
                                    'name': '<TAG_NAME>',
                                    'created_at': '<TAG_CREATED_AT>',
                                    'updated_at': '<TAG_UPDATED_AT>',
                                    'user': '<AUTHENTICATED_USER_ID>',
                                    'tasks': [
                                        '<TASK_ID>',
                                    ]
                                }
                            ]
                        }
                    ),
                    OpenApiExample(
                        'All tags response',
                        value={
                            'message': 'Success',
                            'tags': [
                                {
                                    'id': '<TAG_ID>',
                                    'name': '<TAG_NAME>',
                                    'created_at': '<TAG_CREATED_AT>',
                                    'updated_at': '<TAG_UPDATED_AT>',
                                    'user': '<AUTHENTICATED_USER_ID>',
                                    'tasks': [
                                        '<TASK_ID>',
                                    ]
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
                        'No selector was provided',
                        value={
                            'selector': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid task id',
                        value={
                            'message': 'Invalid task ID'
                        }
                    ),
                    OpenApiExample(
                        'Invalid selector value',
                        value={
                            'message': 'Invalid "selector" parameter'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Tag not found',
                        value={
                            'message': 'Tag not found'
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
        tags=['Tags'],
        summary='Create/Connect/Disconnect tags',
        description='With this endpoint you can do these 4 actions:\n\n1-Create a tag\n\n2-Connect an existing tag to an existing task\n\n3-Create a tag and connect it to existing task with 1 request\n\n4-Disconnect a tag from an existing task if they are connected' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='action',
                description='The action to perform.',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Create a tag',
                        value='create'
                    ),
                    OpenApiExample(
                        'Connect to an existing task',
                        value='connect'
                    ),
                    OpenApiExample(
                        'Create and connect to an existing task',
                        value='create-connect'
                    ),
                    OpenApiExample(
                        'Disconnect from an existing task',
                        value='disconnect'
                    )
                ]
            ),
            OpenApiParameter(
                name='name',
                description='Tag name(should be less than 30 characters). Is required if action is "create" or "create-connect"',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Tag name',
                        value='<TAG_NAME: anything shorter than 30 characters>',
                    )
                ]
            ),
            OpenApiParameter(
                name='task_id',
                description='Task ID. Is required when action is "connect" or "create-connect" or "disconnect"',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Task ID',
                        value='1'
                    )
                ]
            ),
            OpenApiParameter(
                name='tag_id',
                description='Tag ID. Is required when action is "connect" or "disconnect"',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Tag ID',
                        value='1'
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'action': {
                        'type': 'string',
                        'example': 'create',
                        'description': 'Action to perform',
                    },
                    'name': {
                        'type': 'string',
                        'example': 'chores',
                        'description': 'Tag name',
                    },
                    'task_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'Task ID',
                    },
                    'tag_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'Tag ID',
                    }
                },
                'required': ['action'],
                'examples': {
                    'Valid create request': {
                        'value': {
                            'action': 'create',
                            'name': 'chores'
                        },
                        'description': 'Creates a tag with the name chores'
                    },
                    'Valid connect request': {
                        'value': {
                            'action': 'connect',
                            'tag_id': '1',
                            'task_id': '1'
                        },
                        'description': 'Connects the tag with ID 1 to the task with ID 1 if they exist'
                    },
                    'Valid create-connect request': {
                        'value': {
                            'action': 'connect',
                            'name': 'chores',
                            'task_id': '1'
                        },
                        'description': 'Creates a tag with the name chores and connects it to the task with ID 1 if the task exists'
                    },
                    'Valid disconnect request': {
                        'value': {
                            'action': 'disconnect',
                            'tag_id': '1',
                            'task_id': '1'
                        },
                        'description': 'Disconnects tag with ID 1 from task with ID 1 if they are connected'
                    },
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Connect/Disconnect was successful',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Tag connected response',
                        value={
                            'message': 'Connected tag(<TAG_ID>) to task(<TASK_ID>)',
                        }
                    ),
                    OpenApiExample(
                        'Tag disconnected response',
                        value={
                            'message': 'Disconnected tag(<TAG_ID>) from task(<TASK_ID>)',
                        }
                    )
                ]
            ),
            201: OpenApiResponse(
                description='Create/Create-Connect was successful',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Tag created response',
                        value={
                            'message': 'Tag created successfully',
                            'tag': {
                                'id': '<TAG_ID>',
                                'name': '<TAG_NAME>',
                                'created_at': '<TAG_CREATED_AT>',
                                'updated_at': '<TAG_UPDATED_AT>',
                                'user': '<AUTHENTICATED_USER_ID>',
                                'tasks': [
                                    '<TASK_ID>',
                                ]
                            }
                        }
                    ),
                    OpenApiExample(
                        'Tag created and connected response',
                        value={
                            'message': 'Tag created and connected successfully',
                            'tag': {
                                'id': '<TAG_ID>',
                                'name': '<TAG_NAME>',
                                'created_at': '<TAG_CREATED_AT>',
                                'updated_at': '<TAG_UPDATED_AT>',
                                'user': '<AUTHENTICATED_USER_ID>',
                                'tasks': [
                                    '<TASK_ID>',
                                ]
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
                        'No action was provided',
                        value={
                            'action': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid action',
                        value={
                            'message': 'Invalid "action" parameter'
                        }
                    ),
                    OpenApiExample(
                        'No name was provided(for create/create-connect)',
                        value={
                            'message': 'When creating a tag, name is required',
                            'name': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid name',
                        value={
                            'name': ['ERRORS']
                        }
                    ),
                    OpenApiExample(
                        'Invalid task_id(for connect/create-connect/disconnect)',
                        value={
                            'message': 'Invalid "task_id" parameter'
                        }
                    ),
                    OpenApiExample(
                        'No task_id was provided(for connect/create-connect/disconnect)',
                        value={
                            'task_id': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'No tag_id was provided(for connect/disconnect)',
                        value={
                            'tag_id': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid tag_id(for connect/disconnect)',
                        value={
                            'message': 'Invalid "tag_id" parameter'
                        }
                    ),
                    OpenApiExample(
                        'Failed to complete action',
                        value={
                            'message': 'Failed to complete the action'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Task not found(for connect/create-connect/disconnect)',
                        value={
                            'message': 'Task not found'
                        }
                    ),
                    OpenApiExample(
                        'Tag not found(for connect/disconnect)',
                        value={
                            'message': 'Tag not found'
                        }
                    )
                ]
            ),
            406: OpenApiResponse(
                description='Tag not connected to task',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Tag not connected',
                        value={
                            'message': 'tag(<TAG_ID>) is not connected to task(<TASK_ID>)',
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }

    ),
    patch=extend_schema(
        tags=['Tags'],
        summary='Edit tags',
        description='Edit tags name' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='name',
                description='New tag name(should be less than 30 characters)',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Tag name',
                        value='<TAG_NAME: anything shorter than 30 characters>',
                    )
                ]
            ),
            OpenApiParameter(
                name='tag_id',
                description='ID of the tag you want to edit.',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Tag ID',
                        value='1'
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'example': 'chores',
                        'description': 'New tag name',
                    },
                    'tag_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'Tag ID',
                    }
                },
                'required': ['name', 'tag_id'],
                'examples': {
                    'Valid create request': {
                        'value': {
                            'tag_id': '1',
                            'name': 'new'
                        },
                        'description': 'Changes the name of tag with ID 1 to "new"'
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
                        'Successfully edited tag',
                        value={
                            'message': 'Tag updated successfully',
                            'tag': {
                                'id': '<TAG_ID>',
                                'name': '<NEW_TAG_NAME>',
                                'created_at': '<TAG_CREATED_AT>',
                                'updated_at': '<TAG_UPDATED_AT>',
                                'user': '<AUTHENTICATED_USER_ID>',
                                'tasks': [
                                    '<TASK_ID>',
                                ]
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
                        'No tag_id was provided',
                        value={
                            'tag_id': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'No name was provided',
                        value={
                            'name': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid tag_id parameter',
                        value={
                            'message': 'Invalid "tag_id" parameter'
                        }
                    ),
                    OpenApiExample(
                        'Invalid name',
                        value={
                            'name': ['ERRORS']
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Tag not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Tag not found',
                        value={
                            'message': 'Tag not found'
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    ),
    delete=extend_schema(
        tags=['Tags'],
        summary='Delete tag(s)',
        description='Delete tags in 3 modes:\n\n1-Single tag by ID\n\n2-Multiple tags by comma-separated IDs\n\n3-All tags connected to authenticated user' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='selector',
                description='Select tag(s) to delete',
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        'Single tag',
                        value='1'
                    ),
                    OpenApiExample(
                        'Multiple tags',
                        value='1,2,3'
                    ),
                    OpenApiExample(
                        'All tags',
                        value='all'
                    )
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'selector': {
                        'type': 'string',
                        'example': '1',
                        'description': 'Tags to delete',
                    }
                },
                'required': ['selector'],
                'examples': {
                    'Valid create request': {
                        'value': {
                            'selector': '1,2,3'
                        },
                        'description': 'Delete tags with IDs of 1, 2 or 3'
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
                        'Single tag deleted',
                        value={
                            'message': 'Deleted 1 tag successfully'
                        }
                    ),
                    OpenApiExample(
                        'Multiple tags deleted',
                        value={
                            'message': 'Deleted <NUMBER_OF_DELETED_TAGS> tag(s) successfully'
                        }
                    ),
                    OpenApiExample(
                        'All tags deleted',
                        value={
                            'message': 'Deleted all(<NUMBER_OF_DELETED_TAGS>) tag(s) successfully'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Bad request',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No selector was provided',
                        value={
                            'selector': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid selector',
                        value={
                            'message': 'Invalid "selector" parameter'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Single tag not found',
                        value={
                            'message': 'Tag not found'
                        }
                    ),
                    OpenApiExample(
                        'Multiple tags not found',
                        value={
                            'message': 'No tag was found to delete'
                        }
                    ),
                    OpenApiExample(
                        'All tags not found',
                        value={
                            'message': 'There is no tag to delete'
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    )
)
class TagView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tags'

    def get(self, request):
        try:
            selector = self.get_data(request, 'selector')['selector']
        except ValidationError as e:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        if self.is_id(selector):
            try:
                tag = request.user.tags.get(id=selector)
                return self.build_response(
                    status.HTTP_200_OK,
                    message='Success',
                    tag=TagSerializer(tag).data
                )
            except Tag.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Tag not found'
                )

        if 'task:' in selector:
            task_id = selector.split(':')[1]

            if not self.is_id(task_id):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Invalid task ID'
                )

            try:
                task = request.user.tasks.get(id=task_id)
                return self.build_response(
                    status.HTTP_200_OK,
                    message='Success',
                    tags=TagSerializer(task.tags.all(), many=True).data
                )
            except Task.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )

        if selector == 'all':
            return self.build_response(
                status.HTTP_200_OK,
                message='Success',
                tags=TagSerializer(request.user.tags.all(), many=True).data
            )

        return self.build_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid "selector" parameter'
        )

    def post(self, request):
        try:
            action = self.get_data(request, 'action')['action']
        except ValidationError as e:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        if action not in ('create', 'connect', 'create-connect', 'disconnect'):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                message='Invalid "action" parameter'
            )

        if action == 'create':
            try:
                data = self.get_data(request, 'name')
            except ValidationError as e:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='When creating a tag, name is required',
                    **e.detail
                )

            serializer = TagSerializer(data=data)

            if not serializer.is_valid():
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    **serializer.errors
                )

            serializer.save(user=request.user)
            return self.build_response(
                status.HTTP_201_CREATED,
                message='Tag created successfully',
                tag=serializer.data
            )

        if action == 'create-connect':
            try:
                data = self.get_data(request, 'name', 'task_id')

                if not self.is_id(data['task_id']):
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST,
                        message='Invalid "task_id" parameter'
                    )
                task = request.user.tasks.get(id=data['task_id'])
            except ValidationError as e:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    **e.detail
                )
            except Task.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )


            serializer = TagSerializer(data=data)

            if not serializer.is_valid():
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    **serializer.errors
                )

            tag = serializer.save(user=request.user)
            tag.tasks.add(task)

            return self.build_response(
                status.HTTP_201_CREATED,
                message='Tag created and connected successfully',
                tag=serializer.data
            )

        if action in ('connect', 'disconnect'):
            try:
                data = self.get_data(request, 'task_id', 'tag_id')
            except ValidationError as e:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    **e.detail
                )

            if not self.is_id(data['tag_id']):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Invalid "tag_id" parameter'
                )

            if not self.is_id(data['task_id']):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Invalid "task_id" parameter'
                )

            try:
                task = request.user.tasks.get(id=data['task_id'])
                tag = request.user.tags.get(id=data['tag_id'])
                if action == 'connect':
                    task.tags.add(tag)
                    return self.build_response(
                        status.HTTP_200_OK,
                        message=f'Connected tag({tag.id}) to task({task.id})'
                    )
                else:
                    if tag not in task.tags.all():
                        return self.build_response(
                            status.HTTP_406_NOT_ACCEPTABLE,
                            message=f'tag({tag.id}) is not connected to task({task.id})'
                        )
                    task.tags.remove(tag)
                    return self.build_response(
                        status.HTTP_200_OK,
                        message=f'Disconnected tag({tag.id}) from task({task.id})'
                    )
            except Task.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )
            except Tag.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Tag not found'
                )

        # Failed to complete an action
        return self.build_response(
            status.HTTP_400_BAD_REQUEST,
            message='Failed to complete the action'
        )

    def patch(self, request):
        try:
            data = self.get_data(request, 'tag_id', 'name')

            if not self.is_id(data['tag_id']):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Invalid "tag_id" parameter'
                )
            tag = request.user.tags.get(id=data['tag_id'])
        except ValidationError as e:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **e.detail
            )
        except Tag.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                message='Tag not found'
            )

        serializer = TagSerializer(instance=tag, data=data, partial=True)

        if not serializer.is_valid():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **serializer.errors
            )

        serializer.save()

        return self.build_response(
            status.HTTP_200_OK,
            message='Tag updated successfully',
            tag=serializer.data
        )

    def delete(self, request):
        try:
            selector = self.get_data(request, 'selector')['selector']
        except ValidationError as e:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **e.detail
            )

        if self.is_id(selector):
            try:
                tag = request.user.tags.get(id=selector)
                tag.delete()
                return self.build_response(
                    status.HTTP_200_OK,
                    message='Deleted 1 tag successfully'
                )
            except Tag.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Tag not found'
                )

        if ',' in selector:
            ids = filter(self.is_id, selector.split(','))
            tags = request.user.tags.filter(id__in=ids)
            if not tags.exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='No tag was found to delete'
                )
            to_delete = tags.count()
            tags.delete()
            return self.build_response(
                status.HTTP_200_OK,
                message=f'Deleted {to_delete} tag(s) successfully'
            )

        if selector == 'all':
            tags = request.user.tags.all()
            if not tags.exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='There is no tag to delete'
                )
            to_delete = tags.count()
            tags.delete()
            return self.build_response(
                status.HTTP_200_OK,
                message=f'Deleted all({to_delete}) tag(s) successfully'
            )

        return self.build_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid "selector" parameter'
        )
