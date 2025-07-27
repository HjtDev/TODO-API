from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .otp import OTP
from .models import User, phone_validator
from rest_framework import status
from TODO_V2.mixins import GetDataMixin, ResponseBuilderMixin
from TODO_V2.utility import send_sms
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, OpenApiParameter
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, OutstandingToken, BlacklistedToken
from .serializers import UserSerializer
import logging


logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        # Metadata
        operation_id='1',
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
                        'example': '09121234567',
                        'description': 'Phone Number'
                    }
                },
                'required': ['phone'],
                'examples': {
                    'Valid Request': {
                        'value': {'phone': '+989121234567'},
                        'description': 'Proper E.164 format'
                    },
                    'Invalid Request': {
                        'value': {'phone': '9123456789'},
                        'description': 'Missing country code'
                    }
                }
            }
        },

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
            extra = {'register': data['phone']}

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


@extend_schema_view(
    post=extend_schema(
        operation_id='2',
        tags=['Authentication'],
        summary='Complete Authentication',
        description='Complete authentication with the phone number that was used in "Start Authentication" and OTP token for verification.',

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
            ),
            OpenApiParameter(
                name='token',
                description='OTP token',
                required=True,
                type=str,
                examples=[
                    OpenApiExample('Valid', value='1234'),
                    OpenApiExample('Invalid', value='12c4'),
                ]
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'phone': {
                        'type': 'string',
                        'example': '09121234567',
                        'description': 'Phone Number'
                    },
                    'token': {
                        'type': 'string',
                        'example': '1234',
                        'description': 'OTP Token'
                    }
                },
                'required': ['phone', 'token'],
                'examples': {
                    'Valid Request': {
                        'value': {
                            'phone': '09123456789',
                            'token': '1234'
                        },
                        'description': 'Proper phone and token'
                    },
                    'Invalid Request': {
                        'value': {
                            'phone': '9123456789',
                            'token': '1234'
                        },
                        'description': 'Invalid phone number format'
                    }
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Successful Authentication',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Successful Authentication',
                        value={
                            'message': 'Successful Authentication',
                            'user': {
                                'id': '1',
                                'phone': '09123456789',
                                'email': 'user@gmail.com',
                                'profile': '/media/default.png'
                            },
                            'auth': {
                                'refresh': 'eyJh...',
                                'access': 'eyJh...',
                                'refresh_expires_in': 1754742040,
                                'access_expires_in': 1753449640,
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Bad Request',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No phone',
                        value={
                            'phone': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'No token',
                        value={
                            'token': 'this field is required'
                        }
                    ),
                    OpenApiExample(
                        'Invalid phone format',
                        value={
                            'message': 'Invalid phone format'
                        }
                    ),
                ]
            ),
            403: OpenApiResponse(
                description='User not active (Banned from authentication)',
                response=dict,
                examples=[
                    OpenApiExample(
                        'User not active',
                        value={
                            'message': 'User is not active'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
              description='No Active OTP',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No Active OTP (cooldown has expired)',
                        value={
                            'message': 'There is no active OTP for this phone'
                        }
                    )
                ]
            ),
            406: OpenApiResponse(
                description='Invalid OTP token (OTP is active but the given token is not valid)',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Invalid OTP token',
                        value={
                            'message': 'Invalid OTP token'
                        }
                    )
                ]
            ),
            409: OpenApiResponse(
                description='Conflict(SMS service problem or hashing problem)',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Conflict',
                        value={
                            'message': 'Failed to validate OTP'
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description='Internal Server Error. Found an active OTP but due cache backend problems couldn\'t retrieve it',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Internal Server Error',
                        value={
                            'message': 'Error'
                        }
                    )
                ]
            )
        }
    )
)
class CompleteAuthentication(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'auth_verify'

    def post(self, request):
        try:
            data = self.get_data(request, 'phone', 'token')
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

        otp = OTP(data['phone'])
        success, result = otp.validate_otp(data['token'])

        if not success:
            if result == 'OTP_MISMATCH':
                return self.build_response(
                    response_status=status.HTTP_409_CONFLICT,
                    message='Failed to validate OTP'
                )
            elif result == 'NO_ACTIVE_OTP':
                return self.build_response(
                    response_status=status.HTTP_404_NOT_FOUND,
                    message='There is no active OTP for this phone'
                )
            elif result == 'NO_TOKEN_FOUND':
                return self.build_response(
                    response_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message='Failed to retrieve OTP token'
                )
            elif result == 'INVALID_OTP_TOKEN':
                return self.build_response(
                    response_status=status.HTTP_406_NOT_ACCEPTABLE,
                    message='Invalid OTP token'
                )
            else:
                return self.build_response(
                    response_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message='Something went wrong'
                )

        otp.cancel_otp()

        if 'id' in result:  # login
            try:
                user = User.objects.get(id=result['id'])
                if not user.is_active:
                    return self.build_response(
                        response_status=status.HTTP_403_FORBIDDEN,
                        message='User is not active'
                    )

                # Deactivating the existing tokens
                active_tokens = OutstandingToken.objects.filter(user=user)
                if active_tokens.exists():
                    for token in active_tokens:
                        BlacklistedToken.objects.get_or_create(token=token)

                refresh_token = RefreshToken.for_user(user)

                return self.build_response(
                    response_status=status.HTTP_200_OK,
                    message='Successful Authentication.',
                    user=UserSerializer(user).data,
                    auth={
                        'refresh': str(refresh_token),
                        'access': str(refresh_token.access_token),
                        'refresh_expires_in': refresh_token.payload['exp'],
                        'access_expires_in': refresh_token.access_token.payload['exp'],
                    }
                )

            except User.DoesNotExist:
                logger.critical(f'Auth failure for {data["phone"]}', exc_info=True)
                return self.build_response(
                    response_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message='Please try again later'
                )

        if 'register' in result:  # register
            user = User.objects.create_user(phone=result['register'])

            refresh_token = RefreshToken.for_user(user)

            return self.build_response(
                response_status=status.HTTP_200_OK,
                message='Successful Authentication.',
                user=UserSerializer(user).data,
                auth={
                    'refresh': str(refresh_token),
                    'access': str(refresh_token.access_token),
                    'refresh_expires_in': refresh_token.payload['exp'],
                    'access_expires_in': refresh_token.access_token.payload['exp'],
                }
            )

        return self.build_response(
            response_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message='Something went wrong, Please try again later'
        )


@extend_schema_view(
    post=extend_schema(
        operation_id='3',
        tags=['Authentication'],
        summary='Renew Access Token',
        description='Renew expired access tokens using refresh token.',

        parameters=[
            OpenApiParameter(
                name='refresh',
                description='Should be a valid and active refresh token.',
                required=True,
                type=str,
            )
        ],

        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {
                        'type': 'string',
                        'example': 'eyJh...',
                        'description': 'Refresh Token.'
                    }
                },
                'required': ['refresh'],
                'examples': {
                    'Valid Example': {
                        'value': {
                            'refresh': 'eyJh...',
                        },
                        'description': 'Proper refresh token format.'
                    }
                }
            }
        },

        responses={
            200: OpenApiResponse(
                description='Successful Generation.',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Successful Generation',
                        value={
                            'message': 'Access Token Generated Successfully',
                            'auth': {
                                'access': 'eyJh...',
                                'access_expires_in': 1753449640,
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Bad Request.',
                response=dict,
                examples=[
                    OpenApiExample(
                        'No refresh token provided.',
                        value={
                            'refresh': 'this field is required',
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description='Blacklisted',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Blacklisted refresh token',
                        value={
                            'message': 'Refresh token is blacklisted.',
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description='Invalid/expired/deactivated refresh token',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Invalid refresh token',
                        value={
                            'message': 'Invalid refresh token.',
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Refresh token payload doesn\'t point to any existing user.',
                response=dict,
                examples=[
                    OpenApiExample(
                        'User not found',
                        value={
                            'message': 'User not found.',
                        }
                    )
                ]
            )
        }
    )
)
class RenewToken(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'auth_renew'

    def post(self, request):
        try:
            data = self.get_data(request, 'refresh')
        except ValidationError as e:
            return self.build_response(
                response_status=status.HTTP_400_BAD_REQUEST,
                message=str(e),
            )

        try:
            refresh = RefreshToken(data['refresh'])
        except (InvalidToken, TokenError) as e:
            return self.build_response(
                response_status=status.HTTP_403_FORBIDDEN,
                message='Invalid refresh token'
            )

        is_allowed = OutstandingToken.objects.filter(
            token=str(refresh),
            expires_at__gt=timezone.now(),
        ).exclude(
            blacklistedtoken__isnull=False,
        ).exists()

        if not is_allowed:
            return self.build_response(
                response_status=status.HTTP_401_UNAUTHORIZED,
                message='Refresh token is blacklisted'
            )

        if not 'phone' in refresh:
            return self.build_response(
                response_status=status.HTTP_404_NOT_FOUND,
                message='User not found'
            )

        try:
            user = User.objects.get(phone=refresh['phone'])
        except User.DoesNotExist:
            return self.build_response(
                response_status=status.HTTP_404_NOT_FOUND,
                message='User not found'
            )

        access = AccessToken.for_user(user)

        return self.build_response(
            response_status=status.HTTP_200_OK,
            message='Access Token Generated Successfully',
            auth={
                'access': str(access),
                'access_expires_in': access.payload['exp'],
            }
        )