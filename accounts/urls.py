from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RequestOTP, VerifyOTP

urlpatterns = [
    path('', RequestOTP.as_view()),
    path('verify/', VerifyOTP.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]
