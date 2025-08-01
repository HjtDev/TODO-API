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
