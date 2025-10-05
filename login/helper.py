import datetime

from ippanel import Client

from login.models import MyUser
from asnaf.local_settings import API_MAX_SMS
from random import randint


def create_random_otp():
    return randint(1000, 9999)


# you api key that generated from panel
api_key = API_MAX_SMS


# create client instance
sms = Client(api_key)

# return float64 type credit amount
credit = sms.get_credit()


def send_otp(mobile, otp):
    pattern_values = {
        "code": otp,
    }

    message_id = sms.send_pattern(
        "h38smj57omnkegg",  # pattern code
        "+983000505",  # originator
        mobile,  # recipient
        pattern_values,  # pattern values
    )
    print('OTP: ', otp)


def check_otp_expiration(mobile):
    try:
        user = MyUser.objects.get(mobile=mobile)
        now = datetime.datetime.now()
        otp_time = user.otp_create_time

        diff_time = now - otp_time
        print('diff_time is :', diff_time)

        # بررسی اینکه آیا زمان اختلاف بیشتر از 120 ثانیه است یا خیر
        if diff_time.seconds > 120:  # اگر بیشتر از دو دقیقه بود
            return False
        return True
    except MyUser.DoesNotExist:
        return False