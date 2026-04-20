"""Configuracion del panel admin para entidades operativas."""

# admin expone clases ModelAdmin para gestion interna en Django admin.
from django.contrib import admin

# Modelos registrados para consulta y mantenimiento desde admin.
from .models import ActivityLog, Employee, FinancialOperation, Product, Sale, SaleItem, Service


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Personaliza filtros y busquedas para el catalogo de empleados."""

    list_display = ('full_name', 'role', 'is_active', 'hired_at', 'user')
    list_filter = ('role', 'is_active')
    search_fields = ('full_name', 'phone', 'user__email')
    autocomplete_fields = ('user',)


@admin.register(FinancialOperation)
class FinancialOperationAdmin(admin.ModelAdmin):
    """Facilita auditoria de operaciones con filtros por tipo y fecha."""

    list_display = ('occurred_on', 'kind', 'category', 'amount', 'employee', 'created_by')
    list_filter = ('kind', 'category', 'occurred_on')
    search_fields = ('description', 'employee__full_name', 'created_by__email')
    autocomplete_fields = ('employee', 'created_by')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Presenta eventos de auditoria para trazabilidad administrativa."""

    list_display = ('created_at', 'action', 'entity_type', 'entity_id', 'operation', 'employee', 'performed_by')
    list_filter = ('action', 'entity_type', 'created_at')
    search_fields = ('title', 'details', 'performed_by__email', 'operation__description', 'employee__full_name')
    autocomplete_fields = ('operation', 'employee', 'performed_by')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Gestiona catalogo de servicios con precios activos."""

    list_display = ('name', 'price', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administra productos y control de stock disponible."""

    list_display = ('name', 'sku', 'unit_price', 'stock', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'sku')


class SaleItemInline(admin.TabularInline):
    """Permite inspeccionar el detalle de productos/servicios por venta."""

    model = SaleItem
    extra = 0
    autocomplete_fields = ('product', 'service')
    readonly_fields = ('subtotal',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Muestra ventas de cabecera y sus items relacionados."""

    list_display = ('id', 'occurred_on', 'total_amount', 'employee', 'created_by', 'created_at')
    list_filter = ('occurred_on',)
    search_fields = ('notes', 'employee__full_name', 'created_by__email')
    autocomplete_fields = ('employee', 'created_by')
    inlines = [SaleItemInline]
