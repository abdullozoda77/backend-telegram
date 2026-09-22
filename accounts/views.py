import random
import string
from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from myapp.models import Account
from myapp.serializers import AccountSerializer
from .models import CustomUser, PhoneOTP
from .serializers import RequestOTPSerializer, UserSerializer, VerifyOTPSerializer

OTP_LENGTH = 6
OTP_LIFETIME = timedelta(minutes=5)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)


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

        user, _ = CustomUser.objects.get_or_create(
            phone_number=phone_number, defaults={'username': phone_number},
        )
        account, account_created = Account.objects.get_or_create(
            user=user,
            defaults={
                'fname': serializer.validated_data['fname'],
                'lname': serializer.validated_data['lname'],
                'passport_id': serializer.validated_data['passport_id'],
            },
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'account': AccountSerializer(account).data,
            'is_new_account': account_created,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
