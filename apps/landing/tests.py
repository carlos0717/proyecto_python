"""Pruebas de humo para las rutas publicas del sitio."""

# TestCase provee cliente HTTP y base temporal para validar respuestas.
from django.test import TestCase


class LandingPageTests(TestCase):
    """Verifica que las vistas publicas respondan correctamente."""

    def test_home_page_returns_200(self):
        """Home debe responder 200 para visitantes anonimos."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_pricing_page_returns_200(self):
        """Pricing debe responder 200 para visitantes anonimos."""
        response = self.client.get('/pricing/')
        self.assertEqual(response.status_code, 200)

    def test_features_page_returns_200(self):
        """Features debe responder 200 para visitantes anonimos."""
        response = self.client.get('/features/')
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_returns_200(self):
        """robots.txt debe existir y devolverse como texto plano."""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('User-agent', response.content.decode())
