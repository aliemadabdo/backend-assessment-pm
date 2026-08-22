from django.urls import path
from .views import UserRegisterView, UserLoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="user-login"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]