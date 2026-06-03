# lms/serializers/common_serializers.py
from rest_framework import serializers
from ..models import Grade, Subject, Chapter, Question


class GradeSerializer(serializers.ModelSerializer):
    """سریالایزر پایه تحصیلی"""

    level_display = serializers.CharField(source='get_level_display', read_only=True)
    subject_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id', 'name', 'level', 'level_display', 'order',
            'is_active', 'subject_count'
        ]

    def get_subject_count(self, obj):
        return obj.subjects.filter(is_active=True).count()


class SubjectSerializer(serializers.ModelSerializer):
    """سریالایزر درس"""

    grade_name = serializers.CharField(source='grade.name', read_only=True)
    grade_level = serializers.CharField(source='grade.level', read_only=True)
    chapter_count = serializers.SerializerMethodField(read_only=True)
    question_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'grade', 'grade_name', 'grade_level',
            'is_active', 'chapter_count', 'question_count'
        ]

    def get_chapter_count(self, obj):
        return obj.chapters.filter(is_active=True).count()

    def get_question_count(self, obj):
        # اصلاح: استفاده از related_name صحیح
        # در مدل Question، فیلد subject داریم و related_name پیش‌فرض 'question_set' است
        return Question.objects.filter(subject=obj, is_active=True).count()


class ChapterSerializer(serializers.ModelSerializer):
    """سریالایزر فصل"""

    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    question_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chapter
        fields = [
            'id', 'name', 'subject', 'subject_name', 'grade', 'grade_name',
            'is_active', 'question_count'
        ]

    def get_question_count(self, obj):
        # اصلاح: استفاده از related_name صحیح
        return Question.objects.filter(chapter=obj, is_active=True).count()