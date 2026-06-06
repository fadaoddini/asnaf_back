# insta/serializers.py
from rest_framework import serializers
from .models import Post, Like, Comment, CommentLike, Story
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """سریالایزر کاربر برای نمایش در پست"""

    class Meta:
        model = User
        fields = ['id', 'mobile', 'first_name', 'last_name', 'image']


class PostSerializer(serializers.ModelSerializer):
    """سریالایزر پست"""
    user = UserSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'post_type', 'media_url', 'caption',
            'likes_count', 'comments_count', 'is_liked', 'created_at'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False

    def get_media_url(self, obj):
        request = self.context.get('request')
        media_url = obj.get_media_url()
        if media_url and request:
            return request.build_absolute_uri(media_url)
        return media_url


class CommentSerializer(serializers.ModelSerializer):
    """سریالایزر کامنت"""
    user = UserSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'text', 'status', 'likes_count',
            'is_liked', 'created_at'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(comment=obj, user=request.user).exists()
        return False


class CommentCreateSerializer(serializers.ModelSerializer):
    """سریالایزر برای ایجاد کامنت"""

    class Meta:
        model = Comment
        fields = ['text']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'pending'  # نیاز به تایید مدیر
        return super().create(validated_data)


class StorySerializer(serializers.ModelSerializer):
    """سریالایزر استوری"""
    user = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Story
        fields = ['id', 'user', 'media_url', 'created_at', 'expires_at', 'is_expired']

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
        elif obj.video:
            url = obj.video.url
        else:
            return None

        if request:
            return request.build_absolute_uri(url)
        return url