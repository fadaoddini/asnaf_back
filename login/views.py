import json
from datetime import datetime
from django.utils import timezone
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
from rest_framework_simplejwt.authentication import JWTAuthentication  # مطمئن شوید که این پکیج را نصب کرده‌اید
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from login import helper
from login.models import MyUser, Follow, Address
from login.serializers import MyUserSerializer, AddressSerializer, MyProfileSerializer, EditProfileSerializer


class SendOtp(APIView):
    def post(self, request, *args, **kwargs):
        print("1111")
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        mobile = body['mobile']
        print(mobile)
        message = "کد تایید با موفقیت ارسال شد"
        status = "ok"
        wait_time = 0  # زمان انتظار

        # دریافت یا ایجاد کاربر
        user, created = MyUser.objects.get_or_create(mobile=mobile)

        print("injam")
        print(user)
        if not created and helper.check_otp_expiration(user.mobile):
            message = "شما به تازگی پیامکی دریافت نموده‌اید و هنوز کد شما معتبر است!"
            status = "failed"

            # محاسبه زمان باقی‌مانده
            now = datetime.now()
            otp_time = user.otp_create_time
            diff_time = now - otp_time

            # زمان باقی‌مانده به ثانیه
            wait_time = 120 - diff_time.seconds if diff_time.seconds < 120 else 0
        else:
            # ارسال OTP
            otp = helper.create_random_otp()
            helper.send_otp(mobile, otp)
            # ذخیره OTP و به‌روزرسانی زمان ارسال
            user.otp = otp
            user.otp_create_time = datetime.now()  # Update OTP creation time
            user.save()

        data = {
            'id': user.id,
            'status': status,
            'message': message,
            'mobile': user.mobile,
            'wait_time': wait_time,  # اضافه کردن زمان انتظار به پاسخ
        }
        return Response(data, content_type='application/json; charset=UTF-8')



class VerifyCode(APIView):
    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        mobile = body['mobile']
        code = body['code']
        # متغیرهای پیش‌فرض
        message = "کد شما صحیح بود"
        status = "ok"
        refresh_token1 = "poooooch"
        access_token1 = "poooooch"

        # جستجوی کاربر با موبایل وارد شده
        user = MyUser.objects.filter(mobile=mobile)

        if user.exists():
            user = user.first()

            # چک کردن اعتبار کد OTP
            if not helper.check_otp_expiration(mobile):
                message = "کد شما اعتبار زمانی خود را از دست داده است لطفا مجددا سعی نمائید!"
                status = "failed"
                data = {
                    'status': status,
                    'messege': message,
                    'refresh_token': refresh_token1,
                    'access_token': access_token1,
                }
                return Response(data, content_type='application/json; charset=UTF-8')

            # چک کردن صحت کد وارد شده
            if user.otp != int(code):
                message = "کد وارد شده صحیح نیست. لطفاً دوباره تلاش کنید."
                status = "failed"
                data = {
                    'status': status,
                    'messege': message,
                    'refresh_token': refresh_token1,
                    'access_token': access_token1,
                }
                return Response(data)

            # اگر کد صحیح است، کاربر فعال می‌شود
            user.is_active = True
            user.save()

            # ایجاد توکن‌های جدید برای کاربر
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh)
            access_token = str(refresh.access_token)

            # ارسال پاسخ با توکن‌ها
            data = {
                'status': status,
                'messege': message,
                'refresh_token': refresh_token,
                'access_token': access_token,
                'user_id': user.pk,
            }
            return Response(data, content_type='application/json; charset=UTF-8')

        else:
            # اگر کاربر پیدا نشد
            message = "کاربری با اطلاعات فوق وجود ندارد!"
            status = "failed"
            data = {
                'status': status,
                'messege': message,
                'refresh_token': refresh_token1,
                'access_token': access_token1
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