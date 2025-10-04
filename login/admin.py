from django.contrib import admin

from login.models import MyUser, Follow

admin.site.register(MyUser)


admin.site.register(Follow)