from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for logging in with JWT-token.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer
    
    @swagger_auto_schema(
        operation_id="Login with JWT token",
        operation_description="Get authentication tokens with email, password, and OTP.",
        request_body=CustomTokenObtainPairSerializer,
        responses={
            200: openapi.Response(
                description="Login succesful",
                schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'auth_token': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                })
            ),
            400: openapi.Response(
            description="Bad request. Email is required or user with this email doesn't exist.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        },
        tags=['Authentication'],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get("user")
        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_user(user)
        response_data = {
            "auth_token": str(access_token),
            "refresh_token": str(refresh_token),
        }
        return Response(response_data, status=status.HTTP_200_OK)


class TokenLogoutView(APIView):
    """
    View for logging out and deleting the current user's auth token.
    """

    permission_classes = (IsAuthenticated,)
    @swagger_auto_schema(
        operation_id="Logout with JWT token",
        operation_description="Logout user and delete JWT token.",
        responses={
            204: openapi.Response(
                description="No content. Auth token successfully deleted.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={204: "No Content"}
                )
            ),
            401: openapi.Response(
                description="Unauthorized. Authentication credentials were not provided.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        tags=['Authentication'],
    )
    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
        except Exception:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
