from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


class Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account")
    fname = models.CharField(max_length=150)
    lname = models.CharField(max_length=150)
    passport_id = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.fname} {self.lname}"


def default_expair():
    return timezone.now() + timedelta(days=365 * 5)


class Card(models.Model):
    CARD_TYPES = (
        ("visa", "Visa"),
        ("credit", "Credit"),
        ("master", "Master"),
        ("simple", "Simple"),
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="cards")
    card_id = models.CharField(max_length=16, unique=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cart_name = models.CharField(max_length=20, choices=CARD_TYPES)
    cvv = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    expair = models.DateTimeField(default=default_expair)

    def __str__(self):
        return self.card_id


class Transaction(models.Model):
    TRANSFER_TYPES = (("phone_num", "Phone Number"), ("card", "Card"))
    STATUS_CHOICES = (("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed"))

    type = models.CharField(max_length=20, choices=TRANSFER_TYPES)
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="sent_transactions")
    reciver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="received_transactions")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    cuur_balance_sender = models.DecimalField(max_digits=14, decimal_places=2)
    cuur_balance_reciver = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")

    def __str__(self):
        return f"{self.sender} -> {self.reciver}: {self.amount}"


class TransactionInside(models.Model):
    TRANSFER_TYPES = (("phone_num", "Phone Number"), ("card", "Card"))
    STATUS_CHOICES = (("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed"))

    type = models.CharField(max_length=20, choices=TRANSFER_TYPES)
    sender = models.CharField(max_length=20)
    reciver = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    cuur_balance_sender = models.DecimalField(max_digits=14, decimal_places=2)
    cuur_balance_reciver = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")

    def __str__(self):
        return f"{self.sender} -> {self.reciver}: {self.amount}"


class GetCredit(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"))

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="credits")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    procent = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="approved")

    def __str__(self):
        return f"Credit {self.amount} for {self.card}"


class PutDeposit(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed"))

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="deposits")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    procent = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")

    def __str__(self):
        return f"Deposit {self.amount} for {self.card}"


class AccountBlackList(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="blacklist_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Blacklisted account {self.account}"


class CardBlackList(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="blacklist_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Blacklisted card {self.card}"
