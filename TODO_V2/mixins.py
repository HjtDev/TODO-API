from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status


class GetDataMixin:
    def get_data(self, request, *args):
        data = request.query_params if request.method == 'GET' else request.data
        result = dict()
        for key in args:
            if not data.get(key):
                raise ValidationError({key: 'this field is required.'})
            result[key] = data[key]

        return result


class ResponseBuilderMixin:
    def build_response(self, response_status: status = status.HTTP_200_OK, **kwargs):
        return Response(data=kwargs, status=response_status)