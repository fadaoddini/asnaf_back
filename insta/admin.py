# insta/admin.py
from django.contrib import admin
from .models import Post, Like, Comment, CommentLike, Story


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post_type', 'likes_count', 'comments_count', 'is_active', 'created_at']
    list_filter = ['post_type', 'is_active', 'created_at']
    search_fields = ['user__mobile', 'caption']
    list_editable = ['is_active']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'text_preview', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__mobile', 'text']
    list_editable = ['status']
    actions = ['approve_comments', 'reject_comments']

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'متن کامنت'

    def approve_comments(self, request, queryset):
        queryset.update(status='approved')
        # به‌روزرسانی تعداد کامنت‌های پست
        for comment in queryset:
            comment.post.comments_count = comment.post.comments.filter(status='approved').count()
            comment.post.save()
        self.message_user(request, f"{queryset.count()} کامنت تایید شد.")

    approve_comments.short_description = "تایید کامنت‌های انتخاب شده"

    def reject_comments(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} کامنت رد شد.")

    reject_comments.short_description = "رد کامنت‌های انتخاب شده"


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'user', 'created_at']


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['created_at']