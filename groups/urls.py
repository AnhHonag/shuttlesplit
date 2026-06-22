from django.urls import path
from . import views, bank_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/join/', views.join_group, name='join_group'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/settings/', views.group_settings, name='group_settings'),
    path('groups/<int:pk>/toggle-active/', views.toggle_group_active, name='toggle_group_active'),
    path('groups/<int:pk>/add-member/', views.add_member, name='add_member'),
    path('groups/<int:group_pk>/members/<int:member_pk>/edit/', views.edit_member, name='edit_member'),
    path('groups/<int:group_pk>/members/<int:member_pk>/remove/', views.remove_member, name='remove_member'),
    path('groups/<int:pk>/deposit/', views.deposit_view, name='deposit'),
    path('groups/<int:pk>/debt-report/', views.debt_report, name='debt_report'),
    path('groups/<int:pk>/member-balances/', views.member_balances, name='member_balances'),
    path('groups/<int:pk>/members/<int:member_pk>/remind/', views.send_debt_reminder, name='send_debt_reminder'),
    # Bank API
    path('api/banks/', bank_views.api_banks, name='api_banks'),
    path('api/bank/lookup/', bank_views.api_lookup_account, name='api_bank_lookup'),
]
