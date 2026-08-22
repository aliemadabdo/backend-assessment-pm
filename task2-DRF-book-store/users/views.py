from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema
from django.db import IntegrityError

from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["username", "password"],
        }
    },
    responses={
        201: {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "email": {"type": "string"},
                "token": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
            },
        },
    },
)
class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            return Response(
                {
                    "username": user.username,
                    "email": user.email,
                    "token": token,
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {"detail": "Could not create user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        }
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "token": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
            },
        },
    },
)
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            return Response(
                {
                    "username": user.username,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )