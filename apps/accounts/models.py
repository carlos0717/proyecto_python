"""Modelos de autenticacion: usuario personalizado y su manager."""

# AbstractUser y BaseUserManager permiten reemplazar username por email.
from django.contrib.auth.models import AbstractUser, BaseUserManager
# models define los campos persistidos y relaciones de la entidad usuario.
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager que centraliza la creacion de usuarios y superusuarios."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea un usuario normal validando email y aplicando hash al password."""
        if not email:
            raise ValueError('Email is required')
        role = extra_fields.get('role')
        if role and 'user_type' not in extra_fields:
            extra_fields['user_type'] = CustomUser.UserType.COLLABORATOR
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea un superusuario con permisos de staff y rol administrador."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.Role.ADMIN)
        extra_fields.setdefault('user_type', CustomUser.UserType.COLLABORATOR)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Usuario del sistema autenticado por email y segmentado por rol."""

    class Role(models.TextChoices):
        """Roles funcionales para controlar acceso a vistas y datos."""

        ADMIN = 'admin', 'Administrador'
        MANAGER = 'gerente', 'Gerente'
        EMPLOYEE = 'empleado', 'Empleado'

    class UserType(models.TextChoices):
        """Clasifica la cuenta para separar cliente de colaborador interno."""

        CLIENT = 'cliente', 'Cliente'
        COLLABORATOR = 'colaborador', 'Colaborador'

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.CLIENT)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def is_manager(self):
        """Indica si el usuario tiene permisos de gestion (admin o gerente)."""
        return self.role in {self.Role.ADMIN, self.Role.MANAGER}

    @property
    def is_collaborator(self):
        """Indica si la cuenta pertenece a personal interno del negocio."""
        return self.user_type == self.UserType.COLLABORATOR

    def __str__(self):
        """Representacion legible usada en admin, logs y depuracion."""
        return self.email
