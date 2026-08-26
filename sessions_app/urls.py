from django.urls import path
from . import views
urlpatterns = [
    path('groups/<int:group_pk>/sessions/', views.session_list, name='session_list'),
    path('groups/<int:group_pk>/sessions/create/', views.create_session_view, name='create_session'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/edit/', views.edit_session, name='edit_session'),
    path('my-sessions/', views.my_sessions, name='my_sessions'),
]
