from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from login.views import SendOtp, VerifyCode, VerifyNameApi, \
    SetImageUser, LogoutV1, GetInfo, FollowAPIView, UnFollowAPIView, IsFollowAPIView, \
    UserDetailsFollowingAPIView, AddressListCreateView, AddressDetailView, CheckTokenMobile, ProfileInfoApi, CheckToken, \
    EditProfileView

urlpatterns = [

    path('sendOtp', SendOtp.as_view(), name='send-otp'),
    path('verifyName', VerifyNameApi.as_view(), name='verify-name-api'),
    path('v1/setImageUser', SetImageUser.as_view(), name='set-image-user'),
    path('v1/getInfo', GetInfo.as_view(), name='get-info'),
    path('v1/follow/', FollowAPIView.as_view(), name='follow'),
    path('v1/unfollow/', UnFollowAPIView.as_view(), name='unfollow'),
    path('v1/isFollowing/<int:user_id>/', IsFollowAPIView.as_view(), name='is-following'),
    path('v1/userDetails/<int:user_id>', UserDetailsFollowingAPIView.as_view(), name='user-details-following'),
    path('v1/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/address/', AddressListCreateView.as_view(), name='address-list-create-v1'),
    path('v1/address/<uuid:pk>/', AddressDetailView.as_view(), name='address-detail-v1'),

    path('v1/verifyCodeMob', VerifyCode.as_view(), name='verify-mob'),
    path('v1/checkTokenMobile', CheckTokenMobile.as_view(), name='check-token'),


    path('v1/sendOtp', SendOtp.as_view(), name='send-otp-v1'),
    path('v1/logout', LogoutV1.as_view(), name='logout-v1'),
    path('v1/checkToken', CheckToken.as_view(), name='check-token-v1'),
    path('v1/verifyCode', VerifyCode.as_view(), name='verify'),
    path('v1/refreshToken', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/profile/info', ProfileInfoApi.as_view(), name='profile-info-v1'),
    path('v1/edit_profile_user', EditProfileView.as_view(), name='edit-profile-user'),
]
