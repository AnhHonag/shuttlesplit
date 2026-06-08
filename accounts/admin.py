from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'email', 'phone', 'is_active']
    fieldsets = UserAdmin.fieldsets + (('Extra', {'fields': ('full_name', 'phone', 'avatar')}),)
