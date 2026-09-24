from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    ChangePassword, Logout, Profile, Register, RequestOTP, SetOffline, SetOnline,
    UserDetail, UserList, VerifyOTP,
)

urlpatterns = [
    path('register/', Register.as_view()),
    path('token/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('otp/request/', RequestOTP.as_view()),
    path('otp/verify/', VerifyOTP.as_view()),
    path('profile/', Profile.as_view()),
    path('logout/', Logout.as_view()),
    path('change-password/', ChangePassword.as_view()),
    path('online/', SetOnline.as_view()),
    path('offline/', SetOffline.as_view()),
    path('users/', UserList.as_view()),
    path('users/<int:pk>/', UserDetail.as_view()),
]
