from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import Question
from ..serializers import (
    QuestionSerializer,
    QuestionListSerializer,
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
)
from .base import BaseAPIView


class QuestionListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionListSerializer


    def get_queryset(self):
        user = self.request.user

        # فقط معلم مجاز است سوالات خود را ببیند
        if not hasattr(user, 'teacher_profile'):
            return Question.objects.none()

        teacher = user.teacher_profile
        queryset = Question.objects.filter(teacher=teacher, is_active=True)

        # فیلتر بر اساس پایه
        grade_id = self.request.query_params.get('grade_id')
        if grade_id:
            queryset = queryset.filter(grade_id=grade_id)

        # فیلتر بر اساس درس
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        # فیلتر بر اساس فصل
        chapter_id = self.request.query_params.get('chapter_id')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)

        # فیلتر بر اساس درجه سختی
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        return queryset


# lms/views/question_views.py
class QuestionCreateView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # فقط معلم مجاز است
        if not hasattr(request.user, 'teacher_profile'):
            return self.error_response(
                message="فقط معلمان می‌توانند سوال ایجاد کنند",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = QuestionCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            # این خط را اضافه کنید تا خطاهای دقیق را ببینید
            print("Serializer errors:", serializer.errors)
            return self.error_response(
                message="خطای اعتبارسنجی",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        question = serializer.save()
        response_serializer = QuestionSerializer(question)

        return self.success_response(
            data=response_serializer.data,
            message="سوال با موفقیت ایجاد شد",
            status_code=status.HTTP_201_CREATED
        )


class QuestionDetailView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk, is_active=True)
        except Question.DoesNotExist:
            return self.error_response(message="سوال یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # بررسی دسترسی
        if hasattr(request.user, 'teacher_profile'):
            if question.teacher != request.user.teacher_profile:
                return self.error_response(message="شما به این سوال دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)
        elif not request.user.is_superuser:
            return self.error_response(message="شما به این سوال دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        serializer = QuestionSerializer(question)
        return self.success_response(data=serializer.data)


class QuestionUpdateView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return self.error_response(message="سوال یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند ویرایش کند
        if not hasattr(request.user, 'teacher_profile') or question.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این سوال دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        serializer = QuestionUpdateSerializer(question, data=request.data, partial=True)

        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        question = serializer.save()
        response_serializer = QuestionSerializer(question)

        return self.success_response(
            data=response_serializer.data,
            message="سوال با موفقیت بروزرسانی شد"
        )


class QuestionDeleteView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return self.error_response(message="سوال یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند حذف کند
        if not hasattr(request.user, 'teacher_profile') or question.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این سوال دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        question.is_active = False
        question.save()

        return self.success_response(message="سوال با موفقیت حذف شد")