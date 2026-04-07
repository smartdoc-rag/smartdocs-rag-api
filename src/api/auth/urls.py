from django.urls import path
from src.api.auth.views import (
    RegisterView,
    LoginView,
    MeView,
    ResetPasswordView,
    RefreshTokenView,
    LogoutView,
)

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
    path("me", MeView.as_view()),
    path("reset-password", ResetPasswordView.as_view()),
    path("reset-token", RefreshTokenView.as_view()),
    path("logout", LogoutView.as_view()),
]
