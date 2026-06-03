# lms/views/common_views.py - بازنویسی کامل

from rest_framework.permissions import AllowAny
from ..models import Grade, Subject, Chapter
from ..serializers import GradeSerializer, SubjectSerializer, ChapterSerializer
from .base import BaseAPIView


class GradeListView(BaseAPIView):
    """لیست پایه‌های تحصیلی"""
    permission_classes = [AllowAny]

    def get(self, request):
        grades = Grade.objects.filter(is_active=True).order_by('order')
        serializer = GradeSerializer(grades, many=True)
        return self.success_response(data=serializer.data)


class SubjectListView(BaseAPIView):
    """لیست دروس بر اساس پایه تحصیلی"""
    permission_classes = [AllowAny]

    def get(self, request):
        grade_id = request.query_params.get('grade_id')
        queryset = Subject.objects.filter(is_active=True)

        if grade_id:
            queryset = queryset.filter(grade_id=grade_id)

        queryset = queryset.order_by('name')
        serializer = SubjectSerializer(queryset, many=True)
        return self.success_response(data=serializer.data)


class ChapterListView(BaseAPIView):
    """لیست فصل‌ها بر اساس درس"""
    permission_classes = [AllowAny]

    def get(self, request):
        subject_id = request.query_params.get('subject_id')
        queryset = Chapter.objects.filter(is_active=True)

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        queryset = queryset.order_by('name')
        serializer = ChapterSerializer(queryset, many=True)
        return self.success_response(data=serializer.data)