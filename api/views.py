from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.tasks import send_otp_email_celery
from users.models import OneTimePassword, User

from .serializers import UserBasicSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):

    permission_classes = (permissions.AllowAny,)
    serializer_class = UserBasicSerializer
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(pk=self.request.user.pk)

    def get_serializer_class(self):
        """
        Get serializer depending on request method.
        """

        if self.action == 'create':
            return UserCreateSerializer
        return UserBasicSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        email = user.email
        otp = user.generate_otp()
        send_otp_email_celery.delay(email, otp)
        user.save()

    @swagger_auto_schema(
        operation_id="Get User List",
        operation_description="Retrieve a list of users.",
        responses={
            200: UserBasicSerializer(many=True),
            403: "Permission Denied"
        },
        tags=['Users'],
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response
        return Response(response.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_id="Get User",
        operation_description="Retrieve a single user.",
        responses={
            200: UserBasicSerializer(many=True),
            403: "Permission Denied"
        },
        tags=['Users'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="Create User",
        operation_description="Create a new user. Need no permissions.",
        request_body=UserCreateSerializer,
        responses={
            200: UserBasicSerializer,
            403: "Permission Denied"
        },
        tags=['Users'],
    )
    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        email = request.data.get("email")
        try:
            existing_user = User.objects.get(username=username, email=email)
            otp = existing_user.generate_otp()
            send_otp_email_celery.delay(email, otp)
            existing_user.save()
            response_data = {
                "email": email,
                "username": username
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            pass

        response = super().create(request, *args, **kwargs)
        response.status_code = status.HTTP_200_OK
        return response

    @swagger_auto_schema(
        operation_id="Patch User",
        operation_description="Update an existing user.",
        request_body=UserBasicSerializer,
        responses={
            200: UserBasicSerializer,
            403: "Permission Denied"
        },
        tags=['Users'],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="Delete User",
        operation_description="Delete an existing user",
        responses={
            204: "No Content",
            403: "Permission Denied"
        },
        tags=['Users'],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_id="Verify account",
    operation_description="Verifying user with OTP that sent to user's email.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'otp': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['email', 'otp'],
    ),
    responses={
        200: openapi.Response(
            description="OTP sent to your email. Now you can log in.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        400: openapi.Response(
            description="Bad request. Email or OTP code is missing or invalid.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        404: openapi.Response(
            description="Not found. User with this email does not exist.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        401: openapi.Response(
            description="Unauthorized. Exceeded maximum tries for OTP verification.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        403: openapi.Response(
            description="Forbidden. Invalid OTP code or email, or email already verified.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        )
    },
    tags=['Authentication'],
)
@api_view(['POST'])
def verify_account(request):
    """
    Endpoint for verifying user account using OTP.
    """

    if request.method == 'POST':
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response(
                {'error': 'Email and OTP code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': "User with this email does not exist."})
        try:
            otp_instance = OneTimePassword.objects.get(user=user, otp=otp)
            if not otp_instance.is_otp_valid():
                return Response(
                    {'error': 'OTP code has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.otp_tries > 5:
                return Response(
                    {'error': 'Exceeded maximum tries for OTP verification'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.verified:
                return Response(
                    {'error': 'Email already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except OneTimePassword.DoesNotExist:
            user.otp_tries += 1
            user.save()
            return Response(
                {'error': 'Invalid OTP code or email'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.otp_tries = 0
        user.verified = True
        user.save()
        otp_instance.delete()
        return Response(
            {'message': 'Account verified successfully. Now you can log in.'},
            status=status.HTTP_200_OK
            )



@swagger_auto_schema(
    method='post',
    operation_id="Generate one time password",
    operation_description="Generate and send OTP to the user's email.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['email'],
    ),
    responses={
        200: openapi.Response(
            description="OTP sent to your email. Now you can log in.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        400: openapi.Response(
            description="Bad request. Email is required or user with this email doesn't exist.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        )
    },
    tags=['Authentication'],
)
@api_view(['POST'])
def get_otp(request):
    """
    Endpoint for generating and sending OTP to the user's email.
    """

    if request.method == 'POST':
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user_instance = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email doesnt exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        otp = user_instance.generate_otp()
        send_otp_email_celery.delay(email, otp)
        return Response(
            {'message': 'OTP sent to your email. Now you can log in.'},
            status=status.HTTP_200_OK
        )
