from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from proj.admin_mixins import SuperuserEditMixin
from .models import User


@admin.register(User)
class UserAdmin(SuperuserEditMixin, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ['email', 'username', 'is_staff', 'is_superuser', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['email']
    readonly_fields = ['created_at']

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'username', 'password1', 'password2')}),
    )
