# lms/views/student_views.py - نسخه ساده بدون ایجاد کاربر
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import Student, Grade
from ..serializers import (
    StudentSerializer,
    StudentListSerializer,
    StudentRegistrationSerializer,
)
from .base import BaseAPIView

MyUser = get_user_model()



class StudentRegisterView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # فقط معلم می‌تواند دانش‌آموز اضافه کند
        if not hasattr(request.user, 'teacher_profile'):
            return self.error_response(
                message="فقط معلمان می‌توانند دانش‌آموز اضافه کنند",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = StudentRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                message="خطا در ثبت‌نام",
                errors=serializer.errors
            )

        data = serializer.validated_data
        mobile = data['mobile']
        teacher = request.user.teacher_profile

        try:
            # بررسی کن دانش‌آموز وجود دارد یا نه
            student, created = Student.objects.get_or_create(
                mobile=mobile,
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'grade_id': data.get('grade_id'),
                    'created_by': teacher  # اضافه کردن معلم ایجاد کننده
                }
            )

            if not created:
                # اگر دانش‌آموز قبلاً وجود داشت و توسط این معلم ایجاد نشده بود
                if student.created_by and student.created_by != teacher:
                    return self.error_response(
                        message="این دانش‌آموز توسط معلم دیگری ثبت شده است",
                        errors={"mobile": "شماره همراه قبلاً توسط معلم دیگری ثبت شده"},
                        status_code=status.HTTP_409_CONFLICT
                    )

                # به‌روزرسانی اطلاعات
                student.first_name = data['first_name']
                student.last_name = data['last_name']
                if data.get('grade_id'):
                    student.grade_id = data['grade_id']
                if not student.created_by:
                    student.created_by = teacher
                student.save()

                return self.success_response(
                    data=StudentSerializer(student).data,
                    message="دانش‌آموز قبلاً ثبت شده بود. اطلاعات به‌روزرسانی شد.",
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.success_response(
                    data=StudentSerializer(student).data,
                    message="دانش‌آموز با موفقیت ثبت شد",
                    status_code=status.HTTP_201_CREATED
                )

        except Exception as e:
            print(f"Unexpected error: {e}")
            return self.error_response(
                message=f"خطای غیرمنتظره: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StudentProfileView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # اگر کاربر لاگین کرده و student_profile دارد
        if hasattr(request.user, 'student_profile') and request.user.student_profile:
            serializer = StudentSerializer(request.user.student_profile)
            return self.success_response(data=serializer.data)

        return self.error_response(
            message="پروفایل دانش‌آموز یافت نشد",
            status_code=status.HTTP_404_NOT_FOUND
        )

    def put(self, request):
        if hasattr(request.user, 'student_profile') and request.user.student_profile:
            student = request.user.student_profile

            if 'first_name' in request.data:
                student.first_name = request.data['first_name']
            if 'last_name' in request.data:
                student.last_name = request.data['last_name']
            if 'grade_id' in request.data:
                student.grade_id = request.data['grade_id']

            student.save()

            serializer = StudentSerializer(student)
            return self.success_response(
                data=serializer.data,
                message="پروفایل با موفقیت بروزرسانی شد"
            )

        return self.error_response(
            message="پروفایل دانش‌آموز یافت نشد",
            status_code=status.HTTP_404_NOT_FOUND
        )


class StudentListView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        mobile = request.query_params.get('mobile')

        # اگر معلم است - فقط دانش‌آموزانی که خودش اضافه کرده را نشان بده
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            students = Student.objects.filter(created_by=teacher)

            if mobile:
                students = students.filter(mobile=mobile)

            serializer = StudentListSerializer(students, many=True)
            return self.success_response(data=serializer.data)

        # اگر ادمین است - همه دانش‌آموزان را نشان بده
        if user.is_superuser:
            students = Student.objects.all()
            if mobile:
                students = students.filter(mobile=mobile)
            serializer = StudentListSerializer(students, many=True)
            return self.success_response(data=serializer.data)

        # اگر خود دانش‌آموز است
        if hasattr(user, 'student_profile'):
            students = Student.objects.filter(id=user.student_profile.id)
            serializer = StudentListSerializer(students, many=True)
            return self.success_response(data=serializer.data)

        return self.success_response(data=[])

class StudentDetailView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # معلم می‌تواند جزئیات دانش‌آموزان دعوت شده را ببیند
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            try:
                student = Student.objects.get(pk=pk, invited_exams__teacher=teacher)
            except Student.DoesNotExist:
                return self.error_response(
                    message="دانش‌آموز یافت نشد یا دسترسی ندارید",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        # ادمین می‌تواند همه را ببیند
        elif request.user.is_superuser:
            try:
                student = Student.objects.get(pk=pk)
            except Student.DoesNotExist:
                return self.error_response(
                    message="دانش‌آموز یافت نشد",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            return self.error_response(
                message="شما دسترسی لازم را ندارید",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = StudentSerializer(student)
        return self.success_response(data=serializer.data)


class StudentDeleteView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return self.error_response(
                message="شما دسترسی لازم را ندارید",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return self.error_response(
                message="دانش‌آموز یافت نشد",
                status_code=status.HTTP_404_NOT_FOUND
            )

        student.delete()

        return self.success_response(message="دانش‌آموز با موفقیت حذف شد")


class StudentByMobileView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mobile = request.query_params.get('mobile')

        if not mobile:
            return self.error_response(message="شماره موبایل را وارد کنید")

        if not hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
            return self.error_response(
                message="شما دسترسی لازم را ندارید",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            student = Student.objects.get(mobile=mobile)
        except Student.DoesNotExist:
            return self.error_response(
                message="دانش‌آموزی با این شماره یافت نشد",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentSerializer(student)
        return self.success_response(data=serializer.data)