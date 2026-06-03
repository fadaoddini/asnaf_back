from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import Teacher, Skill
from ..serializers import (
    TeacherSerializer,
    TeacherListSerializer,
    TeacherRegistrationSerializer,
)
from .base import BaseAPIView
from ..serializers.teacher_serializers import SkillSerializer

MyUser = get_user_model()


class SkillListView(generics.ListAPIView):

    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [AllowAny]
    queryset = Skill.objects.filter(is_active=True)
    serializer_class = SkillSerializer



class SkillCreateView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return self.error_response(
                message="فقط ادمین می‌تواند مهارت جدید ایجاد کند",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = SkillSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        skill = serializer.save()
        return self.success_response(
            data=SkillSerializer(skill).data,
            message="مهارت با موفقیت ایجاد شد",
            status_code=status.HTTP_201_CREATED
        )


# lms/views/teacher_views.py

class TeacherRegisterView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TeacherRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                message="خطا در ثبت‌نام",
                errors=serializer.errors
            )

        data = serializer.validated_data
        user = request.user  # از کاربر لاگین شده استفاده کن

        # بررسی اینکه کاربر قبلاً معلم نشده
        if Teacher.objects.filter(user=user).exists():
            return self.error_response(
                message="این کاربر قبلاً به عنوان معلم ثبت‌نام شده است",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # ایجاد معلم (بدون ایجاد کاربر جدید)
        teacher = Teacher.objects.create(
            user=user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            mobile=data['mobile'],  # شماره موبایل از کاربر
            school_name=data.get('school_name', ''),
            description=data.get('description', ''),
            qualification=data.get('qualification', ''),
            experience=data.get('experience', ''),
        )

        # اضافه کردن مهارت‌ها
        skill_ids = data.get('skill_ids', [])
        if skill_ids:
            teacher.skills.set(skill_ids)

        # پردازش تصویر پروفایل
        profile_image_base64 = data.get('profile_image_base64')
        if profile_image_base64:
            try:
                image_file = self.decode_base64_file(profile_image_base64, f"profile_{teacher.id}.jpg")
                teacher.profile_image = image_file
            except Exception as e:
                pass

        # پردازش مدرک
        certificate_base64 = data.get('certificate_base64')
        certificate_name = data.get('certificate_name')
        if certificate_base64 and certificate_name:
            try:
                ext = certificate_name.split('.')[-1] if '.' in certificate_name else 'pdf'
                cert_file = self.decode_base64_file(certificate_base64, f"cert_{teacher.id}.{ext}")
                teacher.certificate = cert_file
            except Exception as e:
                pass

        teacher.save()

        # پاسخ
        response_serializer = TeacherSerializer(teacher)
        return self.success_response(
            data=response_serializer.data,
            message="ثبت‌نام با موفقیت انجام شد. منتظر تایید ادمین باشید."
        )

    def decode_base64_file(self, base64_string, filename=None):
        """تبدیل base64 به فایل"""
        if not base64_string:
            return None

        try:
            format, imgstr = base64_string.split(';base64,')
            ext = format.split('/')[-1]

            if not filename:
                filename = f"file.{ext}"

            from django.core.files.base import ContentFile
            import base64
            return ContentFile(base64.b64decode(imgstr), name=filename)
        except Exception:
            return None


class TeacherProfileView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return self.error_response(message="پروفایل معلم یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        serializer = TeacherSerializer(teacher)
        return self.success_response(data=serializer.data)

    def put(self, request):
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return self.error_response(message="پروفایل معلم یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        serializer = TeacherSerializer(teacher, data=request.data, partial=True)

        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        serializer.save()
        return self.success_response(data=serializer.data, message="پروفایل با موفقیت بروزرسانی شد")


class TeacherListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    queryset = Teacher.objects.all()
    serializer_class = TeacherListSerializer


    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser:
            return Teacher.objects.none()
        return super().get_queryset()


class TeacherCheckStatusView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            teacher = Teacher.objects.get(user=user)
        except Teacher.DoesNotExist:
            # کاربر معلم نیست
            return self.error_response(
                message="معلم یافت نشد",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # کاربر معلم است - اطلاعات را برمی‌گردانیم
        serializer = TeacherSerializer(teacher)
        return self.success_response(
            data=serializer.data,
            message="اطلاعات معلم یافت شد"
        )