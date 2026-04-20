"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# settings/static habilitan servido de estaticos en modo desarrollo.
from django.conf import settings
from django.conf.urls.static import static
# admin y include/path definen panel interno y enrutamiento modular.
from django.contrib import admin
from django.urls import include, path

# robots_txt expone metadatos para motores de busqueda.
from apps.landing.views import robots_txt

urlpatterns = [
    # Archivo robots para SEO.
    path('robots.txt', robots_txt, name='robots_txt'),
    # Panel administrativo de Django.
    path('admin/', admin.site.urls),
    # Flujo de autenticacion (login/signup/reset) de allauth.
    path('accounts/', include('allauth.urls')),
    # Sitio publico (home, pricing, features).
    path('', include('apps.landing.urls')),
    # Aplicacion interna autenticada.
    path('dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
