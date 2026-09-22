import random
import string
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .filters import filter_transactions
from .models import (
    Account, Card, Transaction, TransactionInside,
    GetCredit, PutDeposit, AccountBlackList, CardBlackList,
)
from .serializers import (
    AccountSerializer, CardSerializer, TransactionSerializer, TransactionInsideSerializer,
    GetCreditSerializer, PutDepositSerializer, AccountBlackListSerializer, CardBlackListSerializer,
)

def generate_card_id():
    while True:
        card_id = ''.join(random.choices(string.digits, k=16))
        if not Card.objects.filter(card_id=card_id).exists():
            return card_id

def generate_cvv():
    return ''.join(random.choices(string.digits, k=3))

class AccountDetail(generics.RetrieveAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.account

class CheckAccountExists(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        phone_number = request.query_params.get('phone_number')
        exists = Account.objects.filter(user__phone_number=phone_number).exists()
        return Response({'exists': exists})

class CardListCreate(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Card.objects.none()
        return Card.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            card_id=generate_card_id(),
            cvv=generate_cvv(),
        )

class CardDetail(generics.RetrieveDestroyAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Card.objects.none()
        return Card.objects.filter(account=self.request.user.account)

class CheckCardExists(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        card_id = request.query_params.get('card_id')
        exists = Card.objects.filter(card_id=card_id).exists()
        return Response({'exists': exists})

class TransactionListCreate(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        account = self.request.user.account
        queryset = Transaction.objects.filter(sender=account) | Transaction.objects.filter(reciver=account)
        return filter_transactions(queryset.distinct(), self.request.query_params)

    def perform_create(self, serializer):
        sender = self.request.user.account
        reciver = serializer.validated_data['reciver']
        amount = serializer.validated_data['amount']

        if amount <= 0:
            raise ValidationError({'amount': 'Amount must be positive'})
        if sender == reciver:
            raise ValidationError({'reciver_id': 'Cannot transfer to your own account'})
        if sender.balance < amount:
            raise ValidationError({'amount': 'Insufficient balance'})

        sender.balance -= amount
        reciver.balance += amount
        sender.save(update_fields=['balance'])
        reciver.save(update_fields=['balance'])

        serializer.save(
            sender=sender,
            cuur_balance_sender=sender.balance,
            cuur_balance_reciver=reciver.balance,
            status='completed',
        )

class TransactionInsideListCreate(generics.ListCreateAPIView):
    serializer_class = TransactionInsideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TransactionInside.objects.none()
        account = self.request.user.account
        identifiers = [account.user.phone_number] + list(account.cards.values_list('card_id', flat=True))
        queryset = TransactionInside.objects.filter(sender__in=identifiers) | TransactionInside.objects.filter(reciver__in=identifiers)
        return filter_transactions(queryset.distinct(), self.request.query_params)

    def perform_create(self, serializer):
        transfer_type = serializer.validated_data['type']
        reciver_value = serializer.validated_data['reciver']
        amount = serializer.validated_data['amount']

        if amount <= 0:
            raise ValidationError({'amount': 'Amount must be positive'})

        sender_account = self.request.user.account

        if transfer_type == 'phone_num':
            reciver_account = Account.objects.filter(user__phone_number=reciver_value).first()
            sender_value = sender_account.user.phone_number
        else:
            reciver_card = Card.objects.filter(card_id=reciver_value).first()
            reciver_account = reciver_card.account if reciver_card else None
            sender_card = self.request.user.account.cards.first()
            sender_value = sender_card.card_id if sender_card else sender_account.user.phone_number

        if not reciver_account:
            raise ValidationError({'reciver': 'Recipient not found'})
        if reciver_account == sender_account:
            raise ValidationError({'reciver': 'Cannot transfer to your own account'})
        if sender_account.balance < amount:
            raise ValidationError({'amount': 'Insufficient balance'})

        sender_account.balance -= amount
        reciver_account.balance += amount
        sender_account.save(update_fields=['balance'])
        reciver_account.save(update_fields=['balance'])

        serializer.save(
            sender=sender_value,
            cuur_balance_sender=sender_account.balance,
            cuur_balance_reciver=reciver_account.balance,
            status='completed',
        )

class GetCreditCreate(generics.ListCreateAPIView):
    serializer_class = GetCreditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GetCredit.objects.none()
        return GetCredit.objects.filter(card__account=self.request.user.account)

    def perform_create(self, serializer):
        card = serializer.validated_data['card']
        amount = serializer.validated_data['amount']

        if card.account != self.request.user.account:
            raise ValidationError({'card': 'Not your card'})
        if card.cart_name != 'credit':
            raise ValidationError({'card': 'Card must be of type credit'})

        card.balance += amount
        card.save(update_fields=['balance'])
        serializer.save(status='approved')

class PutDepositCreate(generics.ListCreateAPIView):
    serializer_class = PutDepositSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PutDeposit.objects.none()
        return PutDeposit.objects.filter(card__account=self.request.user.account)

    def perform_create(self, serializer):
        card = serializer.validated_data['card']
        amount = serializer.validated_data['amount']

        if card.account != self.request.user.account:
            raise ValidationError({'card': 'Not your card'})

        card.balance += amount
        card.save(update_fields=['balance'])
        serializer.save(status='completed')

class AdminAccountList(generics.ListAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminCardList(generics.ListAPIView):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminTransactionList(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return filter_transactions(Transaction.objects.all(), self.request.query_params)

class AccountBlackListListCreate(generics.ListCreateAPIView):
    queryset = AccountBlackList.objects.all()
    serializer_class = AccountBlackListSerializer
    permission_classes = [permissions.IsAdminUser]

class AccountBlackListDetail(generics.RetrieveDestroyAPIView):
    queryset = AccountBlackList.objects.all()
    serializer_class = AccountBlackListSerializer
    permission_classes = [permissions.IsAdminUser]

class CardBlackListListCreate(generics.ListCreateAPIView):
    queryset = CardBlackList.objects.all()
    serializer_class = CardBlackListSerializer
    permission_classes = [permissions.IsAdminUser]

class CardBlackListDetail(generics.RetrieveDestroyAPIView):
    queryset = CardBlackList.objects.all()
    serializer_class = CardBlackListSerializer
    permission_classes = [permissions.IsAdminUser]