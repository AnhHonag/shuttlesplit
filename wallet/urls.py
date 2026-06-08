from django.urls import path
from . import views
urlpatterns = [
    path('groups/<int:group_pk>/wallet/', views.wallet_detail, name='wallet_detail'),
]
