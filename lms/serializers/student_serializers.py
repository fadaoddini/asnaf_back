from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Student, Grade

MyUser = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """سریالایزر کامل دانش‌آموز"""

    full_name = serializers.SerializerMethodField(read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    attempt_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'mobile',
            'grade', 'grade_name', 'registered_at', 'attempt_count'
        ]
        read_only_fields = ['id', 'registered_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_attempt_count(self, obj):
        return obj.attempts.count()


class StudentListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست دانش‌آموزان"""

    full_name = serializers.SerializerMethodField(read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'mobile',
            'grade', 'grade_name', 'registered_at'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"



class StudentRegistrationSerializer(serializers.Serializer):
    """سریالایزر ثبت‌نام دانش‌آموز"""

    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    mobile = serializers.CharField(max_length=11, required=True)
    grade_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_mobile(self, value):
        import re
        if not re.match(r'^09[0-9]{9}$', value):
            raise serializers.ValidationError("شماره همراه معتبر نیست (مثال: 09123456789)")
        return value

    def validate_grade_id(self, value):
        if value:
            from ..models import Grade
            if not Grade.objects.filter(id=value, is_active=True).exists():
                raise serializers.ValidationError("پایه تحصیلی انتخاب شده معتبر نیست")
        return value