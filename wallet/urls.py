from django.urls import path
from . import views
urlpatterns = [
    path('groups/<int:group_pk>/wallet/', views.wallet_detail, name='wallet_detail'),
    path('groups/<int:group_pk>/wallet/transactions/<int:tx_pk>/edit/', views.edit_deposit, name='edit_deposit'),
]
