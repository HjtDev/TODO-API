from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .otp import OTP
from .models import User, phone_validator
from rest_framework import status
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from TODO_V2.utility import send_sms
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, OpenApiParameter, OpenApiTypes, OpenApiRequest
import logging


logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        # Metadata
        tags=['Authentication'],
        summary='Start authentication',
        description='Start authentication with a phone number (works for both login and registration)',

        # 1. Parameters section (ensures parameters panel appears)
        parameters=[
            OpenApiParameter(
                name='phone',
                description='Phone number',
                required=True,
                type=str,
                examples=[
                    OpenApiExample('Valid', value='09121234567'),
                    OpenApiExample('Invalid', value='9123456789')
                ]
            )
        ],

        # 2. Request body schema (for "Try it out" functionality)
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'phone': {
                        'type': 'string',
                        'example': '+989121234567',
                        'description': 'E.164 formatted phone number'
                    }
                },
                'required': ['phone'],
                'examples': {
                    'Valid Example': {
                        'value': {'phone': '+989121234567'},
                        'description': 'Proper E.164 format'
                    },
                    'Invalid Example': {
                        'value': {'phone': '9123456789'},
                        'description': 'Missing country code'
                    }
                }
            }
        },

        # 3. Additional examples (supports older DRF Spectacular versions)
        examples=[
            OpenApiExample(
                'Valid Request',
                value={'phone': '09121234567'},
            ),
            OpenApiExample(
                'Invalid Request',
                value={'phone': '9123456789'},
            )
        ],

        # 4. Comprehensive responses
        responses={
            200: OpenApiResponse(
                description='OTP Sent Successfully',
                response=dict,  # Required for schema generation
                examples=[
                    OpenApiExample(
                        'Success',
                        value={
                            'message': 'OTP sent',
                            'cooldown': 120
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Validation Error',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Missing Field',
                        value={'phone': 'This field is required'}
                    ),
                    OpenApiExample(
                        'Invalid Format',
                        value={'message': 'Invalid phone format'}
                    )
                ]
            ),
            423: OpenApiResponse(
                description='Active OTP Exists',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Cooldown Active',
                        value={
                            'message': 'Existing OTP not expired',
                        }
                    )
                ]
            ),
            429: OpenApiResponse(
                description='Too Many Requests',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Too Many Requests',
                        value={
                            'detail': 'Request was throttled. Expected available in 60 seconds.'
                        }
                    )
                ]
            )
        }
    )
)
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
                message='there is an active OTP please complete the active OTP or wait for expiration',
            )
