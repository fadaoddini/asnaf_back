from django.contrib.auth.backends import ModelBackend
from .models import MyUser


class MobileBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        # استفاده از username به جای mobile
        mobile = username or kwargs.get('mobile')
        if not mobile:
            return None

        try:
            user = MyUser.objects.get(mobile=mobile)
            if user.check_password(password):
                return user
        except MyUser.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return MyUser.objects.get(pk=user_id)
        except MyUser.DoesNotExist:
            return None