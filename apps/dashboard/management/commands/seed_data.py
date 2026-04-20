import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import localdate

from apps.dashboard.models import Employee, FinancialOperation

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with salon demo data (users, employees, and operations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-email',
            default=os.getenv('SEED_ADMIN_EMAIL', 'admin@example.com'),
            help='Email del administrador (default: SEED_ADMIN_EMAIL o admin@example.com)',
        )
        parser.add_argument(
            '--admin-password',
            default=os.getenv('SEED_ADMIN_PASSWORD', 'admin123'),
            help='Password del administrador (default: SEED_ADMIN_PASSWORD o admin123)',
        )
        parser.add_argument(
            '--update-admin-password',
            action='store_true',
            help='Actualizar password de admin si ya existe',
        )
        parser.add_argument(
            '--reset-operations',
            action='store_true',
            help='Eliminar operaciones existentes antes de insertar datos demo',
        )

    def handle(self, *args, **options):
        admin_email = options['admin_email']
        admin_password = options['admin_password']
        update_admin_password = options['update_admin_password']
        reset_operations = options['reset_operations']

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=admin_email,
                defaults={
                    'is_staff': True,
                    'is_superuser': True,
                    'first_name': 'Admin',
                    'role': User.Role.ADMIN,
                },
            )

            if created:
                user.set_password(admin_password)
                user.save(update_fields=['password'])
                self.stdout.write(self.style.SUCCESS(f'Usuario admin creado ({admin_email})'))
            else:
                updates = []
                if not user.is_staff:
                    user.is_staff = True
                    updates.append('is_staff')
                if not user.is_superuser:
                    user.is_superuser = True
                    updates.append('is_superuser')
                if user.role != User.Role.ADMIN:
                    user.role = User.Role.ADMIN
                    updates.append('role')
                if update_admin_password:
                    user.set_password(admin_password)
                    updates.append('password')

                if updates:
                    user.save(update_fields=updates)
                    self.stdout.write(self.style.SUCCESS(f'Usuario admin actualizado ({admin_email})'))
                else:
                    self.stdout.write('Usuario admin ya existe')

            manager_user, _ = User.objects.update_or_create(
                email='gerente@peluqueria.local',
                defaults={
                    'first_name': 'Ana',
                    'last_name': 'Gerente',
                    'role': User.Role.MANAGER,
                    'is_staff': True,
                },
            )
            manager_user.set_password('gerente123')
            manager_user.save(update_fields=['password'])

            employee_user, _ = User.objects.update_or_create(
                email='empleado@peluqueria.local',
                defaults={
                    'first_name': 'Luis',
                    'last_name': 'Estilista',
                    'role': User.Role.EMPLOYEE,
                },
            )
            employee_user.set_password('empleado123')
            employee_user.save(update_fields=['password'])

            employee_1, _ = Employee.objects.update_or_create(
                full_name='Ana Gerente',
                defaults={
                    'role': Employee.Role.MANAGER,
                    'phone': '999111222',
                    'is_active': True,
                    'user': manager_user,
                },
            )
            employee_2, _ = Employee.objects.update_or_create(
                full_name='Luis Estilista',
                defaults={
                    'role': Employee.Role.EMPLOYEE,
                    'phone': '999333444',
                    'is_active': True,
                    'user': employee_user,
                },
            )

            if reset_operations:
                deleted_count, _ = FinancialOperation.objects.all().delete()
                self.stdout.write(self.style.WARNING(f'Se eliminaron {deleted_count} registros previos de operaciones'))

            today = localdate()
            demo_operations = [
                {
                    'kind': FinancialOperation.Kind.INCOME,
                    'category': FinancialOperation.Category.SERVICE,
                    'amount': Decimal('55.00'),
                    'occurred_on': today,
                    'description': 'Corte + lavado',
                    'employee': employee_2,
                },
                {
                    'kind': FinancialOperation.Kind.INCOME,
                    'category': FinancialOperation.Category.PRODUCT,
                    'amount': Decimal('30.00'),
                    'occurred_on': today,
                    'description': 'Venta de shampoo profesional',
                    'employee': employee_1,
                },
                {
                    'kind': FinancialOperation.Kind.EXPENSE,
                    'category': FinancialOperation.Category.OTHER,
                    'amount': Decimal('18.50'),
                    'occurred_on': today,
                    'description': 'Compra de insumos de limpieza',
                    'employee': None,
                },
            ]

            for operation in demo_operations:
                FinancialOperation.objects.create(
                    created_by=user,
                    kind=operation['kind'],
                    category=operation['category'],
                    amount=operation['amount'],
                    occurred_on=operation['occurred_on'],
                    description=operation['description'],
                    employee=operation['employee'],
                )
            self.stdout.write(self.style.SUCCESS('Datos demo insertados (empleados y operaciones)'))

        self.stdout.write(self.style.SUCCESS('\nSeed data completo para Peluqueria Estilo.'))
