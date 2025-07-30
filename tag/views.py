from rest_framework.views import APIView

from task.models import Task
from .serializers import TagSerializer
from .models import Tag
from rest_framework import status
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError


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
                return self.build_response(
                    status.HTTP_200_OK,
                    message=f'Connected tag({tag.id}) to task({task.id})'
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
