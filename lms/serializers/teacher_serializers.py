# lms/serializers/teacher_serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Teacher, Skill
import re
import base64
from django.core.files.base import ContentFile

MyUser = get_user_model()


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'name_en', 'icon', 'category', 'color', 'description']


class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    certificate_url = serializers.SerializerMethodField()
    qualification_display = serializers.CharField(read_only=True)
    experience_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'mobile', 'email',
            'school_name', 'description', 'qualification', 'qualification_display',
            'experience', 'experience_display', 'skills', 'skill_ids',
            'profile_image', 'profile_image_url', 'certificate', 'certificate_url',
            'is_approved', 'status_display', 'registered_at'
        ]
        read_only_fields = ['id', 'registered_at', 'is_approved']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_profile_image_url(self, obj):
        if obj.profile_image and obj.profile_image.name:
            try:
                return obj.profile_image.url
            except:
                return None
        return None

    def get_certificate_url(self, obj):
        if obj.certificate and obj.certificate.name:
            try:
                return obj.certificate.url
            except:
                return None
        return None

    def create(self, validated_data):
        skill_ids = validated_data.pop('skill_ids', [])
        teacher = super().create(validated_data)
        if skill_ids:
            teacher.skills.set(skill_ids)
        return teacher

    def update(self, instance, validated_data):
        skill_ids = validated_data.pop('skill_ids', None)
        teacher = super().update(instance, validated_data)
        if skill_ids is not None:
            teacher.skills.set(skill_ids)
        return teacher


class TeacherListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'mobile',
            'profile_image_url', 'is_approved', 'status_display', 'registered_at'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_profile_image_url(self, obj):
        if obj.profile_image and obj.profile_image.name:
            try:
                return obj.profile_image.url
            except:
                return None
        return None


# lms/serializers/teacher_serializers.py

class TeacherRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    mobile = serializers.CharField(max_length=11, required=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    school_name = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    qualification = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    experience = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    skill_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    profile_image_base64 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    certificate_base64 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    certificate_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_mobile(self, value):
        import re
        if not re.match(r'^09[0-9]{9}$', value):
            raise serializers.ValidationError("شماره همراه معتبر نیست")

        # فقط چک کن که شماره تکراری نباشه (برای معلم دیگه)
        if Teacher.objects.filter(mobile=value).exists():
            raise serializers.ValidationError("این شماره همراه قبلاً ثبت شده است")

        return value

    def validate_skill_ids(self, value):
        from ..models import Skill
        if value:
            existing_ids = set(Skill.objects.filter(id__in=value, is_active=True).values_list('id', flat=True))
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f"مهارت‌های با شناسه‌های {invalid_ids} یافت نشدند")
        return value



