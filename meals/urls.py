from django.urls import path
from . import views

urlpatterns = [
    path('groups/<int:group_pk>/meals/', views.meal_list, name='meal_list'),
    path('groups/<int:group_pk>/meals/create/', views.create_meal, name='create_meal'),
    path('meals/<int:pk>/', views.meal_detail, name='meal_detail'),
    path('meals/<int:pk>/delete/', views.delete_meal, name='delete_meal'),
]
