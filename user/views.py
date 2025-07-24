from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from otp import OTP
from .models import User, phone_validator
from rest_framework import status
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from TODO_V2.utility import send_sms
import logging


logger = logging.getLogger(__name__)


class StartAuthentication(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'auth'

    def post(self, request):
        try:
            data = self.get_data(request, 'phone')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message=str(e),
            )

        try:
            phone_validator(data['phone'])
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message=str(e),
            )

        try:
            user = User.objects.get(phone=data['phone'])
            # Login
            auth_type = 'login'
            extra = {'id': user.id}
        except User.DoesNotExist:
            # Register
            auth_type = 'register'
            extra = {'phone': data['phone']}

        otp = OTP(data['phone'])
        token = otp.generate_token()
        if otp.save_token(token, **extra):
            send_sms(data['phone'], f'{auth_type} with {token}')
            return self.build_response(
                response_status=status.HTTP_200_OK,
                message='OTP token sent successfully.',
                cooldown=otp.expiration_time
            )
        else:
            logger.warning(f'Failed {auth_type} from {data['phone']}')
            return self.build_response(
                response_status=status.HTTP_423_LOCKED,
                message=f'there is an active OTP please complete the active OTP or wait for expiration',
            )
