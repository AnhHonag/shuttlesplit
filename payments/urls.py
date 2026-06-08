from django.urls import path
from . import views
urlpatterns = [
    path('groups/<int:group_pk>/pay/', views.submit_payment, name='submit_payment'),
    path('groups/<int:group_pk>/payments/', views.payment_list, name='payment_list'),
    path('payments/<int:payment_pk>/confirm/', views.confirm_payment_view, name='confirm_payment'),
    path('my-payments/', views.my_payments, name='my_payments'),
    path('groups/<int:group_pk>/members/<int:member_pk>/record-payment/', views.host_record_payment, name='host_record_payment'),
]
