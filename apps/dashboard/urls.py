"""Rutas internas del dashboard autenticado."""

# path declara endpoints y asocia cada URL a su vista correspondiente.
from django.urls import path

# views contiene la logica HTTP de cada funcionalidad del panel.
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Resumen operativo diario y mensual del negocio.
    path('', views.dashboard_home, name='home'),
    # Datos personales del usuario autenticado.
    path('profile/', views.profile, name='profile'),
    # Alta, listado y filtrado de movimientos financieros.
    path('operations/', views.operations, name='operations'),
    # Catalogo de servicios y productos con control de stock.
    path('catalog/', views.catalog, name='catalog'),
    # Registro de ventas con detalle multiproducto/multiservicio.
    path('sales/', views.sales, name='sales'),
    # Exportaciones para analisis externo (Excel/CSV).
    path('operations/export.csv', views.operations_export_csv, name='operations_export_csv'),
    path('operations/export.xlsx', views.operations_export_xlsx, name='operations_export_xlsx'),
    # Gestion de colaboradores y sus estados.
    path('employees/', views.employees, name='employees'),
    path('employees/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:employee_id>/toggle-active/', views.employee_toggle_active, name='employee_toggle_active'),
    # Reportes comparativos por periodos.
    path('reports/', views.reports, name='reports'),
]
