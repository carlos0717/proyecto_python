"""Configuracion del Django admin para el modelo CustomUser."""

# admin y UserAdmin permiten personalizar la gestion de usuarios en panel interno.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# CustomUser es el modelo de autenticacion principal del proyecto.
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Ajusta campos, filtros y formularios de alta para login por email."""

    list_display = ('email', 'user_type', 'role', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'user_type', 'role')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'role', 'password1', 'password2'),
        }),
    )
