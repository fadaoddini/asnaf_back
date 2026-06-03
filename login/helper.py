import datetime
import re
from ippanel import Client
from ippanel.errors import HTTPError
from login.models import MyUser
from asnaf.local_settings import API_MAX_SMS
from random import randint


def create_random_otp():
    return randint(1000, 9999)


api_key = API_MAX_SMS
sms = Client(api_key)


def convert_to_local_number(mobile):
    """
    تبدیل شماره بین‌المللی به فرمت داخلی ایران
    +989135004344 -> 09135004344
    +989135004344 -> 09135004344
    989135004344 -> 09135004344
    """
    # حذف + و کاراکترهای غیرعددی
    clean = re.sub(r'[^\d]', '', mobile)

    # اگر با 98 شروع شده بود تبدیل به 0
    if clean.startswith('98'):
        clean = '0' + clean[2:]

    # اگر با 9 شروع شده بود (بدون صفر) 0 اول اضافه کن
    elif clean.startswith('9') and len(clean) == 10:
        clean = '0' + clean

    return clean


def send_otp(mobile, otp):
    """
    ارسال پیامک با IPPanel
    mobile: شماره به فرمت بین‌المللی مثل +989135004344
    """
    try:
        # تبدیل به فرمت مناسب برای IPPanel
        # اگر شماره ایران است، به فرمت 09135004344 تبدیل کن
        if mobile.startswith('+98'):
            # +989135004344 -> 09135004344
            formatted_mobile = '0' + mobile[3:]
        elif mobile.startswith('98'):
            # 989135004344 -> 09135004344
            formatted_mobile = '0' + mobile[2:]
        else:
            # برای سایر کشورها، + را حذف کن
            formatted_mobile = mobile.lstrip('+')

        pattern_values = {
            "code": str(otp),
        }

        print(f"[SMS] ارسال به: {formatted_mobile}")
        print(f"[SMS] کد: {otp}")

        message_id = sms.send_pattern(
            "lygi1tzxhtkfrhq",  # pattern code
            "+983000505",  # originator
            formatted_mobile,  # recipient
            pattern_values,  # pattern values
        )

        print(f'[SMS] ✅ موفق! شناسه پیام: {message_id}')
        return True

    except Exception as e:
        print(f'[SMS] ❌ خطا: {str(e)}')
        return False


def check_otp_expiration(mobile):
    try:
        user = MyUser.objects.get(mobile=mobile)
        now = datetime.datetime.now()
        otp_time = user.otp_create_time

        diff_time = now - otp_time
        print('diff_time is :', diff_time)

        if diff_time.total_seconds() > 120:
            return False
        return True
    except MyUser.DoesNotExist:
        return False