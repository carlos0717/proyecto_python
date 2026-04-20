"""Rutas publicas de marketing del producto."""

# path registra endpoints de solo lectura para visitantes.
from django.urls import path

# views contiene las paginas de home, features y pricing.
from . import views

app_name = 'landing'

urlpatterns = [
    # Landing principal con propuesta de valor.
    path('', views.home, name='home'),
    # Informacion de planes del servicio.
    path('pricing/', views.pricing, name='pricing'),
    # Catalogo de funcionalidades destacadas.
    path('features/', views.features, name='features'),
]
