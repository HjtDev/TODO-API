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

    def convert_data_to_bool(self, data: str) -> bool:
        return True if data in ('True', 'true', 'yes', 'y', '1', 1) else False

    def is_id(self, value) -> bool:
        return (isinstance(value, str) and value.isdigit() and int(value) > 0) or (isinstance(value, int) and value > 0)


class ResponseBuilderMixin:
    def build_response(self, response_status: status = status.HTTP_200_OK, **kwargs):
        return Response(data=kwargs, status=response_status)