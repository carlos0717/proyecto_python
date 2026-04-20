"""Vistas publicas del sitio: home comercial, pricing, features y robots.txt."""

# HttpResponse se usa para devolver texto plano en robots.txt.
from django.http import HttpResponse
# render arma respuestas HTML usando plantillas.
from django.shortcuts import render
# require_http_methods restringe cada endpoint a metodos permitidos.
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def robots_txt(request):
    """Entrega robots.txt para SEO e indexacion de buscadores."""

    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Sitemap: https://yourdomain.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@require_http_methods(['GET'])
def home(request):
    """Muestra la landing principal con la propuesta de valor del producto."""

    features = [
        {
            'icon': 'cash-register',
            'title': 'Control Diario',
            'description': 'Registra ingresos y egresos por servicios y productos en segundos.',
        },
        {
            'icon': 'users',
            'title': 'Gestion de Empleados',
            'description': 'Administra personal, roles y estado activo desde un solo panel.',
        },
        {
            'icon': 'chart-line',
            'title': 'Reportes',
            'description': 'Visualiza resultados diarios y mensuales para decidir con datos reales.',
        },
        {
            'icon': 'filter',
            'title': 'Filtros por Fecha',
            'description': 'Consulta periodos personalizados para comparar rendimiento del negocio.',
        },
        {
            'icon': 'user-shield',
            'title': 'Roles y Permisos',
            'description': 'Administrador, gerente y empleado con accesos diferenciados.',
        },
        {
            'icon': 'mobile-screen-button',
            'title': 'Interfaz Simple',
            'description': 'Diseñado para equipos pequenos con flujo claro y rapido.',
        },
    ]

    return render(request, 'landing/home.html', {
        'features': features,
    })


@require_http_methods(['GET'])
def pricing(request):
    """Renderiza la pagina publica de precios y planes."""
    return render(request, 'landing/pricing.html')


@require_http_methods(['GET'])
def features(request):
    """Renderiza la pagina publica de funcionalidades clave."""
    return render(request, 'landing/features.html')
