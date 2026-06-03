# lms/views/base.py
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError


class BaseAPIView(APIView):
    """کلاس پایه برای تمام ویوها با JWT"""
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]  # پیش‌فرض احراز هویت

    def success_response(self, data=None, message="عملیات با موفقیت انجام شد", status_code=status.HTTP_200_OK):
        """پاسخ موفقیت آمیز"""
        return Response({
            'success': True,
            'message': message,
            'data': data
        }, status=status_code)

    def error_response(self, message="خطا در انجام عملیات", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """پاسخ خطا"""
        return Response({
            'success': False,
            'message': message,
            'errors': errors
        }, status=status_code)

    def handle_exception(self, exc):
        """مدیریت استثناها"""
        if isinstance(exc, ValidationError):
            return self.error_response(message="خطای اعتبارسنجی", errors=exc.message_dict)

        if isinstance(exc, IntegrityError):
            return self.error_response(message="خطای یکپارچگی داده‌ها", status_code=status.HTTP_409_CONFLICT)

        if isinstance(exc, PermissionError):
            return self.error_response(message="شما دسترسی لازم را ندارید", status_code=status.HTTP_403_FORBIDDEN)

        return self.error_response(
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )