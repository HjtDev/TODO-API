from rest_framework.views import APIView
from rest_framework import status
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter, OpenApiExample
)
from task.models import Task
from .models import Contact
from .serializers import ContactSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from user.views import AUTHENTICATION_REQUIRED, UNAUTHORIZED_RESPONSE, TOO_MANY_REQUESTS_RESPONSE


@extend_schema_view(
    get=extend_schema(
        tags=['Contacts'],
        summary='Get Contact(s)',
        description='Get contacts in 4 modes:\n\n1-Single contact by ID\n\n2-Multiple contact by comma-separated IDs\n\n3-All contacts connected to a task by task ID\n\n4-All contacts connected to authenticated user' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='selector',
                description='Contacts to retrieve',
                type=str,
                required=True,
                examples=[
                    OpenApiExample(
                        'Single contact',
                        value='1'
                    ),
                    OpenApiExample(
                        'Multiple contacts',
                        value='1,2,3'
                    ),
                    OpenApiExample(
                        'All contacts connected to a task',
                        value='task:1'
                    ),
                    OpenApiExample(
                        'All contacts of a authenticated user',
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
                        'description': 'Contacts to retrieve',
                    }
                },
                'required': ['selector'],
                'examples': {
                    'Valid single contact request': {
                        'value': {
                            'selector': '1'
                        },
                        'description': 'Retrieve contact with ID 1 if it exists'
                    },
                    'Valid multiple contacts request': {
                        'value': {
                            'selector': '1,2,3'
                        },
                        'description': 'Retrieve contacts with ID 1, 2 and 3 if each one exists'
                    },
                    'Valid task contacts request': {
                        'value': {
                            'selector': 'task:1'
                        },
                        'description': 'Retrieve all contacts connected to task with ID 1 if it exists'
                    },
                    'Valid all contacts request': {
                        'value': {
                            'selector': 'all'
                        },
                        'description': 'Retrieve all contacts connected to authenticated user'
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
                        'Single contact',
                        value={
                            'message': 'Success',
                            'contact': {
                                'id': '<CONTACT_ID>',
                                'name': '<CONTACT_NAME>',
                                'profile': '<CONTACT_PROFILE>',
                                'created_at': '<CONTACT_CREATED_AT>',
                                'updated_at': '<CONTACT_UPDATED_AT>',
                                'user': '<CONTACT_OWNER_ID>',
                                'tasks': [
                                    '<CONNECTED_TASK_ID>',
                                    '<CONNECTED_TASK_ID>'
                                ]
                            }
                        }
                    ),
                    OpenApiExample(
                        'Multiple contacts',
                        value={
                            'message': 'Success',
                            'contacts': [
                                {
                                    'id': '<CONTACT_ID>',
                                    'name': '<CONTACT_NAME>',
                                    'profile': '<CONTACT_PROFILE>',
                                    'created_at': '<CONTACT_CREATED_AT>',
                                    'updated_at': '<CONTACT_UPDATED_AT>',
                                    'user': '<CONTACT_OWNER_ID>',
                                    'tasks': [
                                        '<CONNECTED_TASK_ID>',
                                        '<CONNECTED_TASK_ID>'
                                    ]
                                }
                            ]
                        }
                    ),
                    OpenApiExample(
                        'All contacts connected to a task',
                        value={
                            'message': 'Success',
                            'contacts': [
                                {
                                    'id': '<CONTACT_ID>',
                                    'name': '<CONTACT_NAME>',
                                    'profile': '<CONTACT_PROFILE>',
                                    'created_at': '<CONTACT_CREATED_AT>',
                                    'updated_at': '<CONTACT_UPDATED_AT>',
                                    'user': '<CONTACT_OWNER_ID>',
                                    'tasks': [
                                        '<CONNECTED_TASK_ID>',
                                        '<CONNECTED_TASK_ID>'
                                    ]
                                }
                            ]
                        }
                    ),
                    OpenApiExample(
                        'All contacts connected to authenticated user',
                        value={
                            'message': 'Success',
                            'contacts': [
                                {
                                    'id': '<CONTACT_ID>',
                                    'name': '<CONTACT_NAME>',
                                    'profile': '<CONTACT_PROFILE>',
                                    'created_at': '<CONTACT_CREATED_AT>',
                                    'updated_at': '<CONTACT_UPDATED_AT>',
                                    'user': '<CONTACT_OWNER_ID>',
                                    'tasks': [
                                        '<CONNECTED_TASK_ID>',
                                        '<CONNECTED_TASK_ID>'
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
                        'Invalid selector',
                        value={
                            'message': 'Invalid "selector" parameter'
                        }
                    ),
                    OpenApiExample(
                        'Invalid task ID',
                        value={
                            'message': 'Invalid task_id'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Contact(s) Not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Single contact',
                        value={
                            'message': 'Contact not found'
                        }
                    ),
                    OpenApiExample(
                        'Multiple contacts',
                        value={
                            'message': 'No contacts found'
                        }
                    ),
                    OpenApiExample(
                        'Task not found',
                        value={
                            'message': 'Task not found'
                        }
                    ),
                    OpenApiExample(
                        'All contacts',
                        value={
                            'message': 'You have no contacts'
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    ),
    post=extend_schema(
        tags=['Contacts'],
        summary='Create/Connect/Disconnect contacts',
        description='You can do these 3 things:\n\n1-Create a new contact\n\n2-Connect a contact to a task if they are not connected\n\n3-Disconnect a contact from task if they are connected' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='action',
                description='The action to take on the contact (create, connect, disconnect)',
                type=str,
                required=True,
                examples=[
                    OpenApiExample(
                        'Create new contact',
                        value='create'
                    ),
                    OpenApiExample(
                        'Connect contact',
                        value='connect'
                    ),
                    OpenApiExample(
                        'Disconnect contact',
                        value='disconnect'
                    )
                ]
            ),
            OpenApiParameter(
                name='name',
                description='The name of the new contact. Required when creating a contact',
                type=str,
                required=False,
                examples=[
                    OpenApiExample(
                        'Contact name',
                        value='<NAME: anything shorter than 60 characters>'
                    )
                ]
            ),
            OpenApiParameter(
                name='profile',
                description='The profile of the new contact. Not required, only for creating user.',
                type=str,
                required=False,
                examples=[
                    OpenApiExample(
                        'Contact profile',
                        value='<PROFILE: any image, maximum 3MB>'
                    )
                ]
            ),
            OpenApiParameter(
                name='contact_id',
                description='The ID of contact. Required when action=connect/disconnect',
                type=str,
                required=False,
                examples=[
                    OpenApiExample(
                        'Contact ID',
                        value='1'
                    )
                ]
            ),
            OpenApiParameter(
                name='task_id',
                description='The ID of task. Required when action=connect/disconnect',
                type=str,
                required=False,
                examples=[
                    OpenApiExample(
                        'Task ID',
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
                        'example': 'Mickael',
                        'description': 'The name of contact',
                    },
                    'profile': {
                        'type': 'image',
                        'example': '<profile.png>',
                        'description': 'The profile picture of contact',
                    },
                    'contact_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'The ID of the contact',
                    },
                    'task_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'The ID of the task',
                    }
                },
                'required': ['action'],
                'examples': {
                    'Valid create contact request': {
                        'value': {
                            'action': 'create',
                            'name': 'Mickael',
                            'profile': '<profile.png>'
                        },
                        'description': 'Creates a contact with the name Mickael',
                    },
                    'Valid connect contacts request': {
                        'value': {
                            'action': 'connect',
                            'contact_id': '1',
                            'task_id': '1'
                        },
                        'description': 'Connects the contact with ID 1 to task with ID 1'
                    },
                    'Valid disconnect contacts request': {
                        'value': {
                            'action': 'disconnect',
                            'contact_id': '1',
                            'task_id': '1'
                        },
                        'description': 'Disconnects the contact with ID 1 to task with ID 1'
                    }
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Connect/Disconnect successful',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Connected contact',
                        value={
                            'message': 'contact(<CONTACT_ID>) has been connected to task(<TASK_ID>)'
                        }
                    ),
                    OpenApiExample(
                        'Already connected',
                        value={
                            'message': 'contact(<CONTACT_ID>) is already connected to task(<TASK_ID>)'
                        }
                    ),
                    OpenApiExample(
                        'Disconnected contact',
                        value={
                            'message': 'contact(<CONTACT_ID>) has been disconnected from task(<TASK_ID>)'
                        }
                    ),
                    OpenApiExample(
                        'Already disconnected',
                        value={
                            'message': 'contact(<CONTACT_ID>) is not connected to task(<TASK_ID>)'
                        }
                    )
                ]
            ),
            201: OpenApiResponse(
                description='Contact created',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Contact created',
                        value={
                            'message': 'Contact created successfully',
                            'contact': {
                                'id': '<CONTACT_ID>',
                                'name': '<CONTACT_NAME>',
                                'profile': '<CONTACT_PROFILE>',
                                'created_at': '<CONTACT_CREATED_AT>',
                                'updated_at': '<CONTACT_UPDATED_AT>',
                                'user': '<CONTACT_OWNER_ID>',
                                'tasks': [
                                    '<CONNECTED_TASK_ID>',
                                    '<CONNECTED_TASK_ID>'
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
                        'No name was provided',
                        value={
                            'message': 'When creating a contact, you must provide a name',
                            'name': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Bad contact fields(name/profile)',
                        value={
                            '<FIELD>': ['FIELD_ERRORS']
                        }
                    ),
                    OpenApiExample(
                        'No contact_id was provided for connect/disconnect',
                        value={
                            'contact_id': 'this field is required',
                        }
                    ),
                    OpenApiExample(
                        'No task_id was provided for connect/disconnect',
                        value={
                            'task_id': 'this field is required',
                        }
                    ),
                    OpenApiExample(
                        'contact_id is not an ID',
                        value={
                            'contact_id': 'invalid contact ID',
                        }
                    ),
                    OpenApiExample(
                        'task_id is not an ID',
                        value={
                            'task_id': 'invalid task ID',
                        }
                    ),
                ]
            ),
            404: OpenApiResponse(
                description='Contact/Task not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Contact not found',
                        value={
                            'message': 'Contact not found'
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

    patch=extend_schema(
        tags=['Contacts'],
        summary='Edit contacts',
        description='Edit contact name and profile' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='contact_id',
                description='ID of the contact you want to edit',
                type=str,
                required=True,
                examples=[
                    OpenApiExample(
                        'Contact ID',
                        value='1'
                    )
                ]
            ),
            OpenApiParameter(
                name='name',
                description='New contact name',
                type=str,
                required=False,
                examples=[
                    OpenApiExample(
                        'Contact name',
                        value='Mickael'
                    )
                ]
            ),
            OpenApiParameter(
                name='profile',
                description='New contact profile',
                type=str,
                required=False,
                examples=[
                    OpenApiExample(
                        'Contact profile',
                        value='new_profile.png'
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
                        'example': 'Mickael',
                        'description': 'New name of the contact',
                    },
                    'profile': {
                        'type': 'image',
                        'example': '<profile.png>',
                        'description': 'New profile picture of the contact',
                    },
                    'contact_id': {
                        'type': 'string',
                        'example': '1',
                        'description': 'The ID of the contact you want to edit',
                    }
                },
                'required': ['contact_id'],
                'examples': {
                    'Valid edit contact request': {
                        'value': {
                            'contact_id': '1',
                            'name': 'Mickael',
                            'profile': '<profile.png>'
                        },
                        'description': 'Edits the contact name and profile if the contact exists',
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
                        'Contact edited',
                        value={
                            'message': 'Contact updated successfully',
                            'contact': {
                                'id': '<CONTACT_ID>',
                                'name': '<CONTACT_NAME>',
                                'profile': '<CONTACT_PROFILE>',
                                'created_at': '<CONTACT_CREATED_AT>',
                                'updated_at': '<CONTACT_UPDATED_AT>',
                                'user': '<CONTACT_OWNER_ID>',
                                'tasks': [
                                    '<CONNECTED_TASK_ID>',
                                    '<CONNECTED_TASK_ID>'
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
                        'No contact_id was provided',
                        value={
                            'contact_id': 'this field is required',
                        }
                    ),
                    OpenApiExample(
                        'contact_id is not an ID',
                        value={
                            'contact_id': 'invalid contact ID',
                        }
                    ),
                    OpenApiExample(
                        'Invalid name/profile',
                        value={
                            '<FIELD>': ['FIELD_ERRORS']
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Contact not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Contact not found',
                        value={
                            'message': 'Contact not found'
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    ),

    delete=extend_schema(
        tags=['Contacts'],
        summary='Delete contact(s)',
        description='Delete contacts in 3 modes:\n\n1-Single contact by ID\n\n2-Multiple contacts by comma-separated IDs\n\n3-All contacts connected to authenticated user' + AUTHENTICATION_REQUIRED,

        parameters=[
            OpenApiParameter(
                name='selector',
                description='contact(s) to delete',
                type=str,
                required=True,
                examples=[
                    OpenApiExample(
                        'Single contact',
                        value='1'
                    ),
                    OpenApiExample(
                        'Multiple contacts',
                        value='1,2,3'
                    ),
                    OpenApiExample(
                        'All contacts',
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
                        'description': 'Contact to delete',
                    }
                },
                'required': ['selector'],
                'examples': {
                    'Valid single contact request': {
                        'value': {
                            'selector': '1'
                        },
                        'description': 'Deletes the contact with ID 1 if it exists',
                    },
                    'Valid multiple contact request': {
                        'value': {
                            'selector': '1,2,3'
                        },
                        'description': 'Deletes the contacts with IDs of 1, 2 and 3 if they exist',
                    },
                    'Valid all contact request': {
                        'value': {
                            'selector': 'all'
                        },
                        'description': 'Deletes all the contacts connected to authenticated user if there is any',
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
                        'Single contact deleted',
                        value={
                            'message': 'Deleted 1 contact successfully'
                        }
                    ),
                    OpenApiExample(
                        'Multiple contact deleted',
                        value={
                            'message': 'Deleted <NUMBER_OF_DELETED_CONTACTS> contact(s) successfully'
                        }
                    ),
                    OpenApiExample(
                        'All contact deleted',
                        value={
                            'message': 'Deleted all(<NUMBER_OF_DELETED_CONTACTS> contact(s) successfully)'
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
                            'message': 'this field is required',
                        }
                    ),
                    OpenApiExample(
                        'Invalid selector',
                        value={
                            'message': 'invalid "selector" parameter'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Contact not found',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Single contact not found',
                        value={
                            'message': 'Contact not found'
                        }
                    ),
                    OpenApiExample(
                        'Multiple contact not found',
                        value={
                            'message': 'No contact was found to delete'
                        }
                    ),
                    OpenApiExample(
                        'All contact not found',
                        value={
                            'message': 'You have no contacts to delete'
                        }
                    )
                ]
            ),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE
        }
    )

)
class ContactAPI(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'contacts'

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
                contact = request.user.contacts.get(id=selector)
                return self.build_response(
                    status.HTTP_200_OK,
                    message='Success',
                    contact=ContactSerializer(contact).data,
                )
            except Contact.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Contact not found'
                )

        if ',' in selector:
            ids = filter(self.is_id, selector.split(','))

            contacts = request.user.contacts.filter(id__in=ids)

            if not contacts.exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='No contact found'
                )

            return self.build_response(
                status.HTTP_200_OK,
                message='Success',
                contacts=ContactSerializer(contacts, many=True).data
            )

        if 'task:' in selector:
            task_id = selector.split(':')[1]

            if not self.is_id(task_id):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Invalid task_id'
                )

            try:
                task = request.user.tasks.get(id=task_id)
                return self.build_response(
                    status.HTTP_200_OK,
                    message='Success',
                    contacts=ContactSerializer(task.contacts.all(), many=True).data
                )
            except Task.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )

        if selector == 'all':
            contacts = request.user.contacts.all()
            if not contacts.exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='You have no contacts'
                )

            return self.build_response(
                status.HTTP_200_OK,
                message='Success',
                contacts=ContactSerializer(contacts, many=True).data
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

        if action == 'create':
            try:
                self.get_data(request, 'name')
            except ValidationError as e:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='When creating a contact, you must provide a name',
                    **e.detail
                )

            serializer = ContactSerializer(data=request.data)  # Passing request.data to also include profile

            if not serializer.is_valid():
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    **serializer.errors
                )

            serializer.save(user=request.user)

            return self.build_response(
                status.HTTP_201_CREATED,
                message='Contact created successfully',
                contact=serializer.data
            )

        if action in ('connect', 'disconnect'):
            try:
                data = self.get_data(request, 'contact_id', 'task_id')

                if not self.is_id(data['contact_id']):
                    raise ValidationError({'contact_id': 'Invalid contact ID'})

                if not self.is_id(data['task_id']):
                    raise ValidationError({'task_id': 'Invalid task ID'})

                contact = request.user.contacts.get(id=data['contact_id'])
                task = request.user.tasks.get(id=data['task_id'])

                connected = task in contact.tasks.all()

                if action == 'connect':
                    if not connected:
                        contact.tasks.add(task)
                        message = f'contact({contact.id}) has been connected to task({task.id})'
                    else:
                        message = f'contact({contact.id}) is already connected to task({task.id})'
                    return self.build_response(
                        status.HTTP_200_OK,
                        message=message
                    )
                else:  # Disconnect
                    if connected:
                        contact.tasks.remove(task)
                        message = f'contact({contact.id}) has been disconnected from task({task.id})'
                    else:
                        message = f'contact({contact.id}) is not connected to task({task.id})'

                    return self.build_response(
                        status.HTTP_200_OK,
                        message=message
                    )

            except ValidationError as e:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    **e.detail
                )
            except Contact.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Contact not found'
                )
            except Task.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Task not found'
                )

        return self.build_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid "action" parameter'
        )

    def patch(self, request):
        try:
            contact_id = self.get_data(request, 'contact_id')['contact_id']

            if not self.is_id(contact_id):
                raise ValidationError({'contact_id': 'Invalid contact ID'})

            contact = request.user.contacts.get(id=contact_id)
        except ValidationError as e:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **e.detail
            )
        except Contact.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                message='Contact not found'
            )

        serializer = ContactSerializer(instance=contact, data=request.data, partial=True)

        if not serializer.is_valid():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **serializer.errors
            )

        serializer.save()

        return self.build_response(
            status.HTTP_200_OK,
            message='Contact updated successfully',
            contact=serializer.data
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
                contact = request.user.contacts.get(id=selector)
                contact.delete()
                return self.build_response(
                    status.HTTP_200_OK,
                    message='Deleted 1 contact successfully'
                )
            except Contact.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='Contact not found'
                )

        if ',' in selector:
            ids = filter(self.is_id, selector.split(','))

            contacts = request.user.contacts.filter(id__in=ids)

            if not contacts.exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='No contact was found to delete'
                )

            to_delete = contacts.count()
            contacts.delete()
            return self.build_response(
                status.HTTP_200_OK,
                message=f'Deleted {to_delete} contact(s) successfully'
            )

        if selector == 'all':
            contacts = request.user.contacts.all()

            if not contacts.exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    message='You have no contacts to delete'
                )

            to_delete = contacts.count()
            contacts.delete()
            return self.build_response(
                status.HTTP_200_OK,
                message=f'Deleted {to_delete} contact(s) successfully'
            )

        return self.build_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid "selector" parameter'
        )
