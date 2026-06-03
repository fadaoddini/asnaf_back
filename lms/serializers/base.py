from rest_framework import serializers
from django.contrib.auth import get_user_model

MyUser = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    """سریالایزر پایه با متدهای مشترک"""

    created_at_fa = serializers.SerializerMethodField(read_only=True)

    def get_created_at_fa(self, obj):
        """تاریخ شمسی"""
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime('%Y/%m/%d %H:%M')
        return None

    def validate_required_field(self, value, field_name, error_message):
        """اعتبارسنجی فیلدهای الزامی"""
        if not value:
            raise serializers.ValidationError({field_name: error_message})
        return value

    def validate_mobile(self, value):
        """اعتبارسنجی شماره همراه"""
        import re
        if not re.match(r'^09[0-9]{9}$', value):
            raise serializers.ValidationError("شماره همراه باید با 09 شروع و 11 رقم باشد")
        return value

    def to_representation(self, instance):
        """تبدیل امن برای جلوگیری از خطاهای JSON"""
        representation = super().to_representation(instance)

        # حذف فیلدهای None
        for key, value in list(representation.items()):
            if value is None:
                representation[key] = ''
            elif isinstance(value, dict):
                pass
            elif hasattr(value, 'isoformat'):
                representation[key] = value.isoformat()

        return representation