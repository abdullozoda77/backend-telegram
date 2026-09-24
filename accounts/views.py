import logging
import random
import string

from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .filters import search_users
from .models import CustomUser, PhoneOTP
from .pagination import CustomPagination
from .serializers import (
    ChangePasswordSerializer, LogoutSerializer, RegisterSerializer,
    RequestOTPSerializer, UserSerializer, VerifyOTPSerializer,
)

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_LIFETIME = timedelta(minutes=5)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)

class Register(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class Profile(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ChangePassword(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SetOnline(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.is_online = True
        request.user.save(update_fields=['is_online'])
        return Response({'is_online': True})

class SetOffline(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.is_online = False
        request.user.save(update_fields=['is_online'])
        return Response({'is_online': False})

class UserList(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = CustomUser.objects.exclude(id=self.request.user.id)
        return search_users(queryset, self.request.query_params)

class UserDetail(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class Logout(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class RequestOTP(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        last_otp = PhoneOTP.objects.filter(phone_number=phone_number).order_by('-created_at').first()
        if last_otp and timezone.now() < last_otp.created_at + OTP_RESEND_COOLDOWN:
            wait = (last_otp.created_at + OTP_RESEND_COOLDOWN - timezone.now()).seconds
            return Response({'detail': f'Please wait {wait}s before requesting a new code'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        code = ''.join(random.choices(string.digits, k=OTP_LENGTH))
        PhoneOTP.objects.create(
            phone_number=phone_number, code=code, expires_at=timezone.now() + OTP_LIFETIME,
        )
        print(f'[OTP] {phone_number}: {code}', flush=True)
        logger.info('OTP for %s: %s', phone_number, code)
        return Response({'detail': 'Code sent', 'expires_in': int(OTP_LIFETIME.total_seconds())}, status=status.HTTP_200_OK)


class VerifyOTP(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer
    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']
        otp = PhoneOTP.objects.filter(
            phone_number=phone_number, code=code, is_used=False,
        ).order_by('-created_at').first()
        if not otp or not otp.is_valid():
            return Response({'detail': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)
        otp.is_used = True
        otp.save(update_fields=['is_used'])

        user, created = CustomUser.objects.get_or_create(
            phone_number=phone_number, defaults={'username': phone_number},
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'is_new_user': created,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)