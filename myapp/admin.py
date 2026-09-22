from django.contrib import admin
from .models import (
    Account, Card, Transaction, TransactionInside,
    GetCredit, PutDeposit, AccountBlackList, CardBlackList,
)

admin.site.register(Account)
admin.site.register(Card)
admin.site.register(Transaction)
admin.site.register(TransactionInside)
admin.site.register(GetCredit)
admin.site.register(PutDeposit)
admin.site.register(AccountBlackList)
admin.site.register(CardBlackList)
