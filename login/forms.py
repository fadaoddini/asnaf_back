from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from login import models
from login.models import MyUser


class RegisterUser(forms.ModelForm):
    class Meta:
        model = models.MyUser
        fields = ['mobile', ]


class NameUserForm(forms.ModelForm):
    class Meta:
        model = models.MyUser
        fields = ['first_name', 'last_name', 'password' ]




class EditProfileForm(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'email']  # فیلدهای قابل ویرایش
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if MyUser.objects.filter(email=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً استفاده شده است.")
        return email


class ChangePasswordForm(PasswordChangeForm):
    """
    فرم برای تغییر رمز عبور
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور فعلی'}),
        label="رمز عبور فعلی"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور جدید'}),
        label="رمز عبور جدید"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'تأیید رمز عبور جدید'}),
        label="تأیید رمز عبور جدید"
    )
