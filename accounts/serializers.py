from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'phone_number']


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)
    fname = serializers.CharField(max_length=150)
    lname = serializers.CharField(max_length=150)
    passport_id = serializers.CharField(max_length=50)
