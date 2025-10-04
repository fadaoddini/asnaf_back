import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from login.myusermanager import MyUserManager
from asnaf import settings


def user_directory_path(instance, filename):
    # فایل را در پوشه image_profile/<uuid>/ ذخیره می‌کند
    return f'image_profile/{uuid.uuid4()}/{filename}'


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')  # برای جلوگیری از فالو دوباره یک کاربر



class MyUser(AbstractUser):
    ONLINE = True
    OFFLINE = False

    ONLINE_OFFLINE = (
        (ONLINE, "online"),
        (OFFLINE, "offline")
    )

    username = None
    mobile = models.CharField(max_length=11, unique=True)
    otp = models.PositiveIntegerField(blank=True, null=True)
    otp_create_time = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
    objects = MyUserManager()
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []
    backend = 'login.mybackend.MobileBackend'

    @classmethod
    def get_user_info(self, pk):
        user = MyUser.objects.filter(pk=pk).first()
        res = user.first_name+" "+user.last_name
        return res

    def follow(self, user):
        """Follow another user."""
        if user != self:
            Follow.objects.get_or_create(follower=self, followed=user)

    def unfollow(self, user):
        """Unfollow another user."""
        Follow.objects.filter(follower=self, followed=user).delete()

    def following(self):
        """Get users that this user is following."""
        return self.following.all()  # 'following' باید 'following' باشد

    def followers(self):
        """Get users that are following this user."""
        return self.followers.all()  # 'followers' باید 'followers' باشد



class Address(models.Model):
    ACTIVE = True
    INACTIVE = False
    STATUS_ADDRESS = (
        (ACTIVE, 'active'),
        (INACTIVE, 'inactive'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    receiver_name = models.CharField(max_length=255)  # نام گیرنده
    address = models.TextField()  # آدرس دقیق
    postal_code = models.CharField(max_length=10)  # کد پستی
    phone = models.CharField(max_length=15)  # شماره تماس
    city = models.CharField(max_length=100)  # شهر
    sub_city = models.CharField(max_length=100)  # محله یا ناحیه
    is_active = models.BooleanField(choices=STATUS_ADDRESS, default=INACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)  # تاریخ ایجاد آدرس
    updated_at = models.DateTimeField(auto_now=True)  # تاریخ آخرین ویرایش آدرس

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.receiver_name} - {self.city}, {self.sub_city}"


