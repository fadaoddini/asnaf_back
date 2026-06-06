# insta/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


def post_image_path(instance, filename):
    """مسیر ذخیره تصاویر پست"""
    return f'insta/posts/{instance.user.id}/{filename}'


def post_video_path(instance, filename):
    """مسیر ذخیره ویدیوهای پست"""
    return f'insta/videos/{instance.user.id}/{filename}'


class Post(models.Model):
    """مدل پست (مشابه اینستاگرام)"""
    POST_TYPES = (
        ('image', 'تصویر'),
        ('video', 'ویدیو'),
        ('story', 'استوری'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insta_posts')

    # نوع پست
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='image')

    # فایل‌های رسانه‌ای
    image = models.ImageField(upload_to=post_image_path, blank=True, null=True, verbose_name="تصویر")
    video = models.FileField(upload_to=post_video_path, blank=True, null=True, verbose_name="ویدیو")

    # محتوا
    caption = models.TextField(blank=True, verbose_name="توضیحات")

    # آمار
    likes_count = models.IntegerField(default=0, verbose_name="تعداد لایک")
    comments_count = models.IntegerField(default=0, verbose_name="تعداد کامنت")

    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "پست"
        verbose_name_plural = "پست‌ها"

    def __str__(self):
        return f"{self.user.mobile} - {self.created_at}"

    def get_media_url(self):
        """دریافت URL رسانه (تصویر یا ویدیو)"""
        if self.image:
            return self.image.url
        elif self.video:
            return self.video.url
        return None


class Like(models.Model):
    """مدل لایک (مشابه اینستاگرام)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insta_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # هر کاربر فقط یک بار می‌تواند لایک کند
        ordering = ['-created_at']
        verbose_name = "لایک"
        verbose_name_plural = "لایک‌ها"

    def __str__(self):
        return f"{self.user.mobile} liked {self.post.id}"


class Comment(models.Model):
    """مدل کامنت (با قابلیت تایید مدیر)"""
    STATUS_CHOICES = (
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insta_comments')
    text = models.TextField(verbose_name="متن کامنت")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")

    # آمار
    likes_count = models.IntegerField(default=0, verbose_name="تعداد لایک کامنت")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "کامنت"
        verbose_name_plural = "کامنت‌ها"

    def __str__(self):
        return f"{self.user.mobile}: {self.text[:30]}"


class CommentLike(models.Model):
    """لایک کامنت"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')


class Story(models.Model):
    """مدل استوری (24 ساعته)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insta_stories')

    image = models.ImageField(upload_to='insta/stories/', blank=True, null=True)
    video = models.FileField(upload_to='insta/stories/videos/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at