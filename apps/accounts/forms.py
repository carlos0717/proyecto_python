"""Formularios de alta y login con validaciones de email enfocadas en UX."""

# re se usa para validar formato basico del email antes de persistir.
import re

# Formularios base de allauth para extender comportamiento sin romper flujo.
from allauth.account.forms import LoginForm, SignupForm
# forms provee validaciones y errores estandar de Django.
from django import forms

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}$")


class CustomSignupForm(SignupForm):
    """Signup con saneamiento y validaciones adicionales de email."""

    user_type = forms.ChoiceField(
        choices=(
            ('cliente', 'Cliente'),
            ('colaborador', 'Colaborador'),
        ),
        initial='cliente',
        required=True,
    )

    def clean_email(self):
        """Normaliza email y valida estructura para reducir errores de registro."""
        email = super().clean_email().strip().lower()

        if not EMAIL_REGEX.match(email):
            raise forms.ValidationError('Por favor, ingresa un correo válido. Ejemplo: usuario@gmail.com')

        local_part, domain = email.split('@', 1)
        if '..' in local_part or '..' in domain:
            raise forms.ValidationError('El correo no puede contener puntos consecutivos.')
        if domain.startswith('.') or domain.endswith('.'):
            raise forms.ValidationError('El dominio del correo no es válido.')

        return email

    def save(self, request):
        """Persiste el tipo de usuario elegido al momento del registro."""
        user = super().save(request)
        selected_type = self.cleaned_data.get('user_type', 'cliente')
        user.user_type = selected_type
        user.save(update_fields=['user_type'])
        return user


class CustomLoginForm(LoginForm):
    """Login que normaliza el identificador para evitar fallos por mayusculas."""

    def clean_login(self):
        """Limpia espacios y fuerza lowercase en el campo login/email."""
        login = self.cleaned_data.get('login', '')
        return login.strip().lower()
