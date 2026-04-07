from django.conf import settings
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from src.api.auth.LoginRequest import LoginRequest
from src.api.auth.RegisterRequest import RegisterRequest
from src.api.auth.ResetPasswordRequest import ResetPasswordRequest
from src.api.user.UserResponse import UserResponse
from src.api._helper import validate_request
from src.api.deps import auth_service, user_service
from src.core.response import (
    created_response,
    fetched_response,
    updated_response,
    deleted_response,
    success_response,
)
from src.core.exceptions import UnauthorizedException
from src.core.auth import require_auth


def _set_refresh_cookie(response, token: str):
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIES_NAME,
        value=token,
        httponly=settings.REFRESH_TOKEN_COOKIES_HTTPONLY,
        samesite=settings.REFRESH_TOKEN_COOKIES_SAMESITE,
        secure=settings.REFRESH_TOKEN_COOKIES_SECURE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response):
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIES_NAME)


class RegisterView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        data = validate_request(RegisterRequest, request.data)
        user = auth_service().register(data)
        return created_response(
            data=UserResponse.from_model(user),
            message="Đăng ký thành công",
        )


class LoginView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        data = validate_request(LoginRequest, request.data)
        result = auth_service().login(data)
        response = success_response(
            data={
                "access_token": result["access_token"],
                "user": UserResponse.from_model(result["user"]),
            },
            message="Đăng nhập thành công",
        )
        _set_refresh_cookie(response, result["refresh_token"])
        return response


class MeView(APIView):
    @require_auth
    def get(self, request):
        user = user_service().get_me(request.user_id)
        return fetched_response(data=UserResponse.from_model(user))


class ResetPasswordView(APIView):
    @require_auth
    def post(self, request):
        data = validate_request(ResetPasswordRequest, request.data)
        auth_service().reset_password(user_id=request.user_id, **data)
        return updated_response(message="Đổi mật khẩu thành công")


class RefreshTokenView(APIView):
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIES_NAME)
        if not raw_refresh:
            raise UnauthorizedException("Không tìm thấy refresh token")
        result = auth_service().refresh_access_token(raw_refresh)
        response = success_response(
            data={"access_token": result["access_token"]},
            message="Làm mới token thành công",
        )
        _set_refresh_cookie(response, result["refresh_token"])
        return response


class LogoutView(APIView):
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIES_NAME)
        if raw_refresh:
            auth_service().logout(raw_refresh)
        response = deleted_response(message="Đăng xuất thành công")
        _clear_refresh_cookie(response)
        return response
