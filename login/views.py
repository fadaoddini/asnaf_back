
import json
import re
from datetime import datetime
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from login import helper
from login.models import MyUser, Follow, Address
from login.serializers import MyUserSerializer, AddressSerializer, MyProfileSerializer, EditProfileSerializer

# لیست کدهای کشورهای پشتیبانی شده
SUPPORTED_COUNTRIES = {
    '98': {'name': 'Iran', 'min_length': 10, 'max_length': 10, 'regex': r'^9\d{9}$'},  # 09123456789 -> 9123456789
    '1': {'name': 'USA/Canada', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '44': {'name': 'UK', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '49': {'name': 'Germany', 'min_length': 10, 'max_length': 11, 'regex': r'^\d{10,11}$'},
    '33': {'name': 'France', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '971': {'name': 'UAE', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '966': {'name': 'Saudi Arabia', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '90': {'name': 'Turkey', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '7': {'name': 'Russia/Kazakhstan', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '86': {'name': 'China', 'min_length': 11, 'max_length': 11, 'regex': r'^\d{11}$'},
    '91': {'name': 'India', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '92': {'name': 'Pakistan', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '93': {'name': 'Afghanistan', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '964': {'name': 'Iraq', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '963': {'name': 'Syria', 'min_length': 8, 'max_length': 9, 'regex': r'^\d{8,9}$'},
    '20': {'name': 'Egypt', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '61': {'name': 'Australia', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '31': {'name': 'Netherlands', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '46': {'name': 'Sweden', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '47': {'name': 'Norway', 'min_length': 8, 'max_length': 8, 'regex': r'^\d{8}$'},
    '45': {'name': 'Denmark', 'min_length': 8, 'max_length': 8, 'regex': r'^\d{8}$'},
    '358': {'name': 'Finland', 'min_length': 9, 'max_length': 10, 'regex': r'^\d{9,10}$'},
    '39': {'name': 'Italy', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '34': {'name': 'Spain', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '351': {'name': 'Portugal', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '30': {'name': 'Greece', 'min_length': 10, 'max_length': 10, 'regex': r'^\d{10}$'},
    '48': {'name': 'Poland', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
    '380': {'name': 'Ukraine', 'min_length': 9, 'max_length': 9, 'regex': r'^\d{9}$'},
}


def validate_and_normalize_mobile(mobile):
    """
    اعتبارسنجی و نرمالایز کردن شماره موبایل
    ورودی: +989123456789 یا 09123456789 یا 9123456789
    خروجی: +989123456789 (فرمت بین‌المللی نرمالایز شده)
    """
    if not mobile:
        return None, "شماره موبایل نمی‌تواند خالی باشد"

    # حذف فضاهای خالی و کاراکترهای اضافی
    mobile = re.sub(r'[\s\-\(\)]', '', mobile.strip())

    # اگر شماره با 00 شروع شده بود تبدیل به +
    if mobile.startswith('00'):
        mobile = '+' + mobile[2:]

    # اگر شماره با صفر شروع شده بود (فرمت داخلی ایران)
    if mobile.startswith('0') and len(mobile) >= 10:
        # حذف صفر اول و اضافه کردن کد ایران
        mobile = '+98' + mobile[1:]

    # اگر شماره با + شروع نشده بود
    if not mobile.startswith('+'):
        # اگر شماره فقط عدد است و طول آن مناسب است، احتمالاً شماره داخلی ایران است
        if mobile.isdigit() and len(mobile) >= 10:
            if len(mobile) == 10:
                mobile = '+98' + mobile
            elif len(mobile) == 11 and mobile.startswith('9'):
                mobile = '+98' + mobile
            else:
                return None, "فرمت شماره موبایل صحیح نیست"
        else:
            return None, "فرمت شماره موبایل صحیح نیست"

    # استخراج کد کشور و شماره محلی
    for country_code, info in SUPPORTED_COUNTRIES.items():
        if mobile.startswith(f'+{country_code}'):
            local_number = mobile[len(f'+{country_code}'):]

            # بررسی طول شماره محلی
            if not (info['min_length'] <= len(local_number) <= info['max_length']):
                return None, f"شماره {info['name']} باید بین {info['min_length']} تا {info['max_length']} رقم باشد"

            # بررسی regex شماره محلی
            if not re.match(info['regex'], local_number):
                return None, f"فرمت شماره {info['name']} صحیح نیست"

            # برگرداندن شماره نرمالایز شده
            normalized = f"+{country_code}{local_number}"
            return normalized, None

    # اگر کد کشور پشتیبانی نشد
    return None, "کد کشور پشتیبانی نمی‌شود"


class SendOtp(APIView):
    def post(self, request, *args, **kwargs):
        print("Sending OTP request received")
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        mobile = body.get('mobile', '')

        print(f"Raw mobile: {mobile}")

        # اعتبارسنجی و نرمالایز کردن شماره
        normalized_mobile, error = validate_and_normalize_mobile(mobile)

        print(f"Normalized mobile: {normalized_mobile}")
        if error:
            return Response({
                'status': 'failed',
                'message': error,
                'wait_time': 0
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"Normalized mobile: {normalized_mobile}")

        message = "کد تایید با موفقیت ارسال شد"
        status_text = "ok"
        wait_time = 0

        # دریافت یا ایجاد کاربر
        user, created = MyUser.objects.get_or_create(mobile=normalized_mobile)

        print(f"User: {user}, Created: {created}")

        if not created and helper.check_otp_expiration(normalized_mobile):
            message = "شما به تازگی پیامکی دریافت نموده‌اید و هنوز کد شما معتبر است!"
            status_text = "failed"

            # محاسبه زمان باقی‌مانده
            now = datetime.now()
            otp_time = user.otp_create_time
            diff_time = now - otp_time
            wait_time = 120 - diff_time.seconds if diff_time.seconds < 120 else 0
        else:
            # ارسال OTP
            otp = helper.create_random_otp()
            helper.send_otp(normalized_mobile, otp)
            user.otp = otp
            user.otp_create_time = datetime.now()
            user.save()

        data = {
            'id': user.id,
            'status': status_text,
            'message': message,
            'mobile': normalized_mobile,
            'wait_time': wait_time,
        }
        return Response(data, content_type='application/json; charset=UTF-8')


class VerifyCode(APIView):
    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        mobile = body.get('mobile', '')
        code = body.get('code', '')

        message = "کد شما صحیح بود"
        status_text = "ok"

        # نرمالایز کردن شماره برای جستجو
        normalized_mobile, error = validate_and_normalize_mobile(mobile)

        if error:
            return Response({
                'status': 'failed',
                'messege': error,
                'refresh_token': '',
                'access_token': '',
            }, status=status.HTTP_400_BAD_REQUEST)

        # جستجوی کاربر
        user = MyUser.objects.filter(mobile=normalized_mobile).first()

        if user:
            # چک کردن اعتبار OTP
            if not helper.check_otp_expiration(normalized_mobile):
                message = "کد شما اعتبار زمانی خود را از دست داده است لطفا مجددا سعی نمائید!"
                status_text = "failed"
                data = {
                    'status': status_text,
                    'messege': message,
                    'refresh_token': '',
                    'access_token': '',
                }
                return Response(data, content_type='application/json; charset=UTF-8')

            # چک کردن صحت کد
            if user.otp != int(code):
                message = "کد وارد شده صحیح نیست. لطفاً دوباره تلاش کنید."
                status_text = "failed"
                data = {
                    'status': status_text,
                    'messege': message,
                    'refresh_token': '',
                    'access_token': '',
                }
                return Response(data)

            # کد صحیح است
            user.is_active = True
            user.save()

            # ایجاد توکن
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh)
            access_token = str(refresh.access_token)

            data = {
                'status': status_text,
                'messege': message,
                'refresh_token': refresh_token,
                'access_token': access_token,
                'user_id': user.pk,
            }
            return Response(data, content_type='application/json; charset=UTF-8')
        else:
            message = "کاربری با اطلاعات فوق وجود ندارد!"
            status_text = "failed"
            data = {
                'status': status_text,
                'messege': message,
                'refresh_token': '',
                'access_token': ''
            }
            return Response(data, content_type='application/json; charset=UTF-8')


class VerifyNameApi(APIView):
    def post(self, request, *args, **kwargs):
        body = request.data  # استفاده از request.data برای دسترسی به داده‌ها

        mobile = body.get('mobile')
        first_name = body.get('first_name')
        last_name = body.get('last_name')
        password = body.get('password')

        # اگر فقط mobile داده شده باشد، چک کردن وجود کاربر
        if mobile and not (first_name or last_name or password):
            my_user = MyUser.objects.filter(mobile=mobile).first()
            if my_user:
                serializer = MyUserSerializer(my_user)
                return Response(serializer.data, content_type='application/json; charset=UTF-8')
            else:
                return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND,
                                content_type='application/json; charset=UTF-8')

        # اگر تمام پارامترها (mobile, first_name, last_name, password) داده شده باشند، بروزرسانی اطلاعات
        if mobile and first_name and last_name and password:
            my_user, created = MyUser.objects.get_or_create(mobile=mobile)
            my_user.first_name = first_name
            my_user.last_name = last_name
            my_user.set_password(password)  # تنظیم رمز عبور
            my_user.save()

            serializer = MyUserSerializer(my_user)
            return Response(serializer.data, status=status.HTTP_200_OK, content_type='application/json; charset=UTF-8')

        # اگر پارامترهای ورودی کامل نباشند
        return Response({'detail': 'Invalid parameters.'}, status=status.HTTP_400_BAD_REQUEST,
                        content_type='application/json; charset=UTF-8')



class GetInfo(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = MyUserSerializer(user)


            return JsonResponse({
                'status': 'ok',
                'user': serializer.data,
            })
        except AuthenticationFailed as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=401)
        except MyUser.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'User not found!'}, status=404)



class SetImageUser(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        user = request.user

        if 'image' not in request.data:
            return Response({"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)

        image = request.data['image']
        user.image = image
        user.save()

        return Response({"message": "Image uploaded successfully!"}, status=status.HTTP_200_OK)



class LogoutV1(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logout(request)
            return Response({"message": "با موفقیت از سیستم خارج شدید"}, status=200)
        except Exception as e:
            return Response({"error": f"خطا در هنگام پردازش درخواست: {str(e)}"}, status=500)




class FollowAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        user_id = body.get('user_id')
        if user_id is None:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        user_to_follow = get_object_or_404(MyUser, id=user_id)
        request.user.follow(user_to_follow)

        followers_count = Follow.objects.filter(followed=user_to_follow).count()
        return Response({
            "status": "success",
            "message": f"Following {user_to_follow.username}",
            "followers": followers_count
        }, status=status.HTTP_201_CREATED)



class UnFollowAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        user_id = body.get('user_id')
        if not user_id:
            return Response({"error": "User ID required"}, status=status.HTTP_400_BAD_REQUEST)

        user_to_unfollow = get_object_or_404(MyUser, id=user_id)
        request.user.unfollow(user_to_unfollow)

        followers_count = Follow.objects.filter(followed=user_to_unfollow).count()
        return Response({
            "status": "success",
            "message": f"Unfollowed {user_to_unfollow.username}",
            "followers": followers_count
        }, status=status.HTTP_204_NO_CONTENT)


class IsFollowAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.is_anonymous:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        user_to_check = get_object_or_404(MyUser, id=user_id)
        is_following = Follow.objects.filter(follower=request.user, followed=user_to_check).exists()

        followers_count = Follow.objects.filter(followed=user_to_check).count()
        following_count = Follow.objects.filter(follower=user_to_check).count()

        return Response({
            "isFollowing": is_following,
            "followers": followers_count,
            "following": following_count
        }, status=status.HTTP_200_OK)




class UserDetailsFollowingAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(MyUser, pk=user_id)

        if request.user.is_anonymous:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        from .serializers import MyProfileSerializer
        serializer = MyProfileSerializer(user, context={'request': request})
        serialized_data = serializer.data

        is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
        serialized_data['isFollowing'] = is_following

        return Response(serialized_data, status=status.HTTP_200_OK,
                        content_type='application/json; charset=UTF-8')



class AddressListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        print("add address to list ....")
        print(serializer)
        print("add address to list ....")
        if serializer.is_valid():
            serializer.save(user=request.user)  # کاربر را به آدرس اضافه می‌کند
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)  # چاپ خطاهای اعتبارسنجی
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AddressDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Address.objects.get(pk=pk, user=self.request.user)  # فقط آدرس‌های متعلق به کاربر فعلی را برمی‌گرداند
        except Address.DoesNotExist:
            return None

    def get(self, request, pk):
        address = self.get_object(pk)
        if address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AddressSerializer(address)
        return Response(serializer.data)

    def put(self, request, pk):
        address = self.get_object(pk)
        if address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AddressSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk)
        if address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckTokenMobile(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # برای اطمینان از احراز هویت اولیه

    def post(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')
        refresh_token = request.data.get('refresh_token')

        # مرحله 1: چک کردن معتبر بودن access_token
        try:
            # اگر access_token معتبر باشد، ادامه می‌دهد
            token = AccessToken(access_token)
            return Response({
                "status": "ok",
                "message": "Access token is valid",
                "access_token": str(token)  # توکن فعلی برمی‌گردد
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            # اگر access_token نامعتبر یا منقضی شده باشد
            if isinstance(e, InvalidToken):
                # مرحله 2: اگر access_token منقضی شده، بررسی refresh_token
                try:
                    refresh = RefreshToken(refresh_token)

                    # ایجاد توکن‌های جدید
                    new_access_token = str(refresh.access_token)
                    new_refresh_token = str(refresh)

                    # بازگشت توکن‌های جدید
                    return Response({
                        "status": "ok",
                        "message": "Access token refreshed",
                        "access_token": new_access_token,
                        "refresh_token": new_refresh_token
                    }, status=status.HTTP_200_OK)

                except TokenError:
                    # اگر refresh_token هم نامعتبر باشد، کاربر باید دوباره لاگین کند
                    return Response({
                        "status": "error",
                        "message": "Refresh token is invalid or expired. Please log in again."
                    }, status=status.HTTP_401_UNAUTHORIZED)

        # برای هر خطای ناشناخته دیگر
        return Response({
            "status": "error",
            "message": "Invalid request."
        }, status=status.HTTP_400_BAD_REQUEST)


class CheckToken(APIView):
    authentication_classes = []
    permission_classes = []

    @csrf_exempt
    def post(self, request):
        access_token = request.headers.get('Authorization', None)
        refresh_token = request.headers.get('x-refresh-token', None)

        if access_token is None:
            raise AuthenticationFailed("Authorization header is missing")

        # حذف "Bearer" از ابتدای توکن
        access_token = access_token.split(" ")[1]

        try:
            # بررسی اعتبار access token
            token = AccessToken(access_token)
            user = token.payload.get('user_id')

            return Response({
                'status': 'ok',
                'message': 'توکن معتبر است',
                'user': str(user),
            }, status=200)

        except Exception:
            if not refresh_token:
                raise AuthenticationFailed("نیازمند رفرش توکن هستیم")

            try:
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)
                new_refresh_token = str(refresh)

                return Response({
                    'status': 'ok',
                    'message': 'توکن جدید ساخته شد',
                    'access_token': new_access_token,
                    'refresh_token': new_refresh_token,
                }, status=200)

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': f'خطا در تولید توکن جدید: {str(e)}',
                }, status=401)



class ProfileInfoApi(generics.GenericAPIView):
    serializer_class = MyProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # اکنون request.user با توجه به توکن احراز هویت، کاربر شناسایی شده است
        profile = MyProfileSerializer(request.user)
        return Response(profile.data, status=status.HTTP_200_OK,
                        content_type='application/json; charset=UTF-8')


class EditProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """برگرداندن اطلاعات کاربر برای فرم ویرایش."""
        user = request.user
        serializer = EditProfileSerializer(user)
        return Response(serializer.data)

    def post(self, request):
        """ذخیره تغییرات اطلاعات کاربر."""
        user = request.user
        serializer = EditProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "اطلاعات با موفقیت ذخیره شد."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckOtpStatus(APIView):
    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        mobile = body.get('mobile')

        try:
            user = MyUser.objects.get(mobile=mobile)
            now = datetime.now()
            otp_time = user.otp_create_time
            diff_time = now - otp_time

            if diff_time.total_seconds() < 120:
                wait_time = 120 - int(diff_time.total_seconds())
                return Response({
                    'status': 'ok',
                    'wait_time': wait_time,
                    'message': 'کد هنوز معتبر است'
                })
            else:
                return Response({
                    'status': 'expired',
                    'wait_time': 0,
                    'message': 'زمان کد منقضی شده است'
                })
        except MyUser.DoesNotExist:
            return Response({
                'status': 'failed',
                'wait_time': 0,
                'message': 'کاربر یافت نشد'
            }, status=404)