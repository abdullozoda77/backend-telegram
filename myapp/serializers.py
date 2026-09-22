from rest_framework import serializers
from .models import (
    Account, Card, Transaction, TransactionInside,
    GetCredit, PutDeposit, AccountBlackList, CardBlackList,
)


class AccountSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'fname', 'lname', 'passport_id', 'balance', 'phone_number']
        read_only_fields = ['balance']


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'account', 'card_id', 'balance', 'cart_name', 'cvv', 'created_at', 'expair']
        read_only_fields = ['account', 'card_id', 'balance', 'cvv', 'created_at', 'expair']


class TransactionSerializer(serializers.ModelSerializer):
    reciver_id = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), source='reciver', write_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'type', 'sender', 'reciver', 'reciver_id', 'amount', 'created_at',
            'cuur_balance_sender', 'cuur_balance_reciver', 'description', 'status',
        ]
        read_only_fields = ['sender', 'reciver', 'cuur_balance_sender', 'cuur_balance_reciver', 'status']


class TransactionInsideSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionInside
        fields = [
            'id', 'type', 'sender', 'reciver', 'amount', 'created_at',
            'cuur_balance_sender', 'cuur_balance_reciver', 'description', 'status',
        ]
        read_only_fields = ['sender', 'cuur_balance_sender', 'cuur_balance_reciver', 'status']


class GetCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = GetCredit
        fields = ['id', 'card', 'amount', 'created_at', 'procent', 'status']
        read_only_fields = ['status']


class PutDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = PutDeposit
        fields = ['id', 'card', 'amount', 'created_at', 'procent', 'status']
        read_only_fields = ['status']


class AccountBlackListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountBlackList
        fields = ['id', 'account', 'created_at', 'description']


class CardBlackListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardBlackList
        fields = ['id', 'card', 'created_at', 'description']
