"""Pruebas de autenticacion y comportamiento del modelo de usuario."""

# get_user_model permite probar contra el modelo auth configurado en settings.
from django.contrib.auth import get_user_model
# TestCase crea base de datos temporal aislada para pruebas unitarias.
from django.test import TestCase

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Valida reglas de creacion de usuarios y flujos basicos de auth."""

    def test_create_user_with_email(self):
        """Un usuario normal se crea con rol por defecto y password hasheado."""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'empleado')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        """El superusuario debe quedar con privilegios administrativos."""
        user = User.objects.create_superuser(email='admin@example.com', password='admin123')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, 'admin')

    def test_create_user_without_email_raises(self):
        """El manager debe rechazar usuarios sin email."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')

    def test_user_str_returns_email(self):
        """La representacion de texto del usuario debe ser su email."""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.assertEqual(str(user), 'test@example.com')

    def test_signup_page_returns_200(self):
        """La pagina de registro debe estar disponible publicamente."""
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_returns_200(self):
        """La pagina de login debe estar disponible publicamente."""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user_without_email_confirmation(self):
        """El flujo de alta debe persistir usuario cuando el formulario es valido."""
        response = self.client.post(
            '/accounts/signup/',
            {
                'email': 'nuevo.usuario@gmail.com',
                'password1': 'Testpass123!!',
                'password2': 'Testpass123!!',
                'user_type': 'cliente',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='nuevo.usuario@gmail.com').exists())

    def test_signup_persists_collaborator_type(self):
        """El registro debe guardar el tipo de usuario seleccionado."""
        response = self.client.post(
            '/accounts/signup/',
            {
                'email': 'colaborador@gmail.com',
                'password1': 'Testpass123!!',
                'password2': 'Testpass123!!',
                'user_type': 'colaborador',
            },
        )
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(email='colaborador@gmail.com')
        self.assertEqual(created_user.user_type, 'colaborador')

    def test_login_with_registered_user_email_and_password(self):
        """Un usuario registrado debe autenticarse con email y password correctos."""
        User.objects.create_user(email='login.user@gmail.com', password='Testpass123!!')
        response = self.client.post(
            '/accounts/login/',
            {
                'login': 'login.user@gmail.com',
                'password': 'Testpass123!!',
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_signup_rejects_invalid_email_format(self):
        """El signup debe rechazar correos con formato invalido."""
        response = self.client.post(
            '/accounts/signup/',
            {
                'email': 'correo-invalido@dominio',
                'password1': 'Testpass123!!',
                'password2': 'Testpass123!!',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid email address')
