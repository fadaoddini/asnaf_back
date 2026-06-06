# portfolio/serializers.py
from rest_framework import serializers
from .models import Project, ProjectImage, ProjectFeature


class ProjectImageSerializer(serializers.ModelSerializer):
    """سریالایزر تصاویر"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectImage
        fields = ['id', 'image_url', 'alt_text_fa', 'alt_text_en', 'order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class ProjectFeatureSerializer(serializers.ModelSerializer):
    """سریالایزر ویژگی‌ها"""

    class Meta:
        model = ProjectFeature
        fields = ['id', 'title_fa', 'title_en', 'order']


class ProjectSerializer(serializers.ModelSerializer):
    """سریالایزر اصلی پروژه - خروجی مناسب برای فرانت‌اند"""
    images = ProjectImageSerializer(many=True, read_only=True)
    features = ProjectFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name_fa', 'name_en', 'description_fa', 'description_en',
            'long_description_fa', 'long_description_en', 'demo_link',
            'order', 'is_active', 'created_at', 'updated_at', 'images', 'features'
        ]

    def to_representation(self, instance):
        """ساختار خروجی رو به فرمت مورد نیاز فرانت‌اند تغییر میده"""
        data = super().to_representation(instance)

        # ساختار جدید برای فرانت‌اند (مشابه قبل)
        return {
            'id': data['id'],
            'name': {
                'fa': data['name_fa'],
                'en': data['name_en']
            },
            'description': {
                'fa': data['description_fa'],
                'en': data['description_en']
            },
            'long_description': {
                'fa': data['long_description_fa'] or data['description_fa'],
                'en': data['long_description_en'] or data['description_en']
            },
            'images': [img['image_url'] for img in data['images']],
            'demo_link': data['demo_link'],
            'features': [
                {'fa': feat['title_fa'], 'en': feat['title_en']}
                for feat in data['features']
            ],
            'order': data['order'],
            'created_at': data['created_at']
        }


class ProjectListSerializer(serializers.ModelSerializer):
    """سریالایزر خلاصه برای لیست"""
    images = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name_fa', 'name_en', 'description_fa', 'description_en', 'demo_link', 'order']

    def get_images(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(first_image.image.url) if request else first_image.image.url
        return None