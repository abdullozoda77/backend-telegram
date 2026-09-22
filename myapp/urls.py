from django.urls import path
from . import views

urlpatterns = [
    path('account/', views.AccountDetail.as_view()),
    path('accounts/check/', views.CheckAccountExists.as_view()),
    path('cards/', views.CardListCreate.as_view()),
    path('cards/<int:pk>/', views.CardDetail.as_view()),
    path('cards/check/', views.CheckCardExists.as_view()),
    path('transactions/', views.TransactionListCreate.as_view()),
    path('transactions/inside/', views.TransactionInsideListCreate.as_view()),
    path('credit/', views.GetCreditCreate.as_view()),
    path('deposit/', views.PutDepositCreate.as_view()),
    path('staff/accounts/', views.AdminAccountList.as_view()),
    path('staff/cards/', views.AdminCardList.as_view()),
    path('staff/transactions/', views.AdminTransactionList.as_view()),
    path('staff/blacklist/accounts/', views.AccountBlackListListCreate.as_view()),
    path('staff/blacklist/accounts/<int:pk>/', views.AccountBlackListDetail.as_view()),
    path('staff/blacklist/cards/', views.CardBlackListListCreate.as_view()),
    path('staff/blacklist/cards/<int:pk>/', views.CardBlackListDetail.as_view()),
]
