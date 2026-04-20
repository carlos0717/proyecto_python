"""Pruebas funcionales del dashboard para acceso, permisos, filtros y auditoria."""

# get_user_model recupera el User real configurado en el proyecto.
from django.contrib.auth import get_user_model
# TestCase crea BD temporal y cliente HTTP para simular requests.
from django.test import TestCase
# localdate asegura fechas consistentes con la zona horaria activa.
from django.utils.timezone import localdate

# Modelos bajo prueba para validar reglas de negocio y persistencia.
from .models import ActivityLog, Employee, FinancialOperation, Product, Sale, Service

User = get_user_model()


class DashboardAccessTests(TestCase):
    """Verifica acceso basico al dashboard segun estado de autenticacion."""

    def test_dashboard_redirects_anonymous(self):
        """Usuarios anonimos deben redirigirse al login en home de dashboard."""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_operations_redirects_anonymous(self):
        """Usuarios anonimos no deben acceder al modulo de operaciones."""
        response = self.client.get('/dashboard/operations/')
        self.assertEqual(response.status_code, 302)

    def test_reports_redirects_anonymous(self):
        """Usuarios anonimos no deben acceder a reportes."""
        response = self.client.get('/dashboard/reports/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_when_logged_in(self):
        """Usuarios autenticados deben acceder correctamente al dashboard."""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_client_user_cannot_access_business_modules(self):
        """Las cuentas cliente no deben ingresar a operaciones, ventas ni reportes."""
        user = User.objects.create_user(
            email='cliente@example.com',
            password='testpass123',
            user_type='cliente',
        )
        self.client.force_login(user)
        self.assertEqual(self.client.get('/dashboard/operations/').status_code, 302)
        self.assertEqual(self.client.get('/dashboard/sales/').status_code, 302)
        self.assertEqual(self.client.get('/dashboard/reports/').status_code, 302)


class HairSalonModelsTests(TestCase):
    """Valida comportamiento de modelos operativos del negocio."""

    def test_create_employee(self):
        """La creacion de empleado debe persistir estado activo por defecto."""
        employee = Employee.objects.create(
            full_name='Ana Ruiz',
            role='gerente',
            phone='999222111',
        )
        self.assertEqual(str(employee), 'Ana Ruiz (Gerente)')
        self.assertTrue(employee.is_active)

    def test_create_financial_operation(self):
        """La operacion financiera debe guardar tipo y categoria solicitados."""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        operation = FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=55,
            occurred_on=localdate(),
            description='Corte de cabello',
            created_by=user,
        )
        self.assertEqual(operation.kind, 'income')
        self.assertEqual(operation.category, 'service')


class EmployeePermissionsTests(TestCase):
    """Comprueba autorizacion por rol para gestionar empleados."""

    def test_employee_cannot_manage_employees_view(self):
        """Rol empleado debe ser bloqueado al abrir administracion de personal."""
        user = User.objects.create_user(email='emp@example.com', password='testpass123', role='empleado')
        self.client.force_login(user)
        response = self.client.get('/dashboard/employees/')
        self.assertEqual(response.status_code, 302)

    def test_manager_can_access_employees_view(self):
        """Rol gerente debe tener acceso al modulo de empleados."""
        user = User.objects.create_user(email='manager@example.com', password='testpass123', role='gerente')
        self.client.force_login(user)
        response = self.client.get('/dashboard/employees/')
        self.assertEqual(response.status_code, 200)

    def test_manager_can_update_employee(self):
        """Gerente debe poder editar datos de un empleado existente."""
        user = User.objects.create_user(email='manager@example.com', password='testpass123', role='gerente')
        employee = Employee.objects.create(full_name='Luis', role='empleado', phone='999111000')
        self.client.force_login(user)

        response = self.client.post(
            f'/dashboard/employees/{employee.id}/update/',
            {
                'full_name': 'Luis Perez',
                'role': 'gerente',
                'phone': '999000111',
                'hired_at': '2026-04-01',
            },
        )
        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.full_name, 'Luis Perez')
        self.assertEqual(employee.role, 'gerente')

    def test_manager_can_toggle_employee_active(self):
        """Gerente debe poder alternar estado activo/inactivo del empleado."""
        user = User.objects.create_user(email='manager@example.com', password='testpass123', role='gerente')
        employee = Employee.objects.create(full_name='Ana', role='empleado', is_active=True)
        self.client.force_login(user)

        response = self.client.post(f'/dashboard/employees/{employee.id}/toggle-active/')
        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertFalse(employee.is_active)


class OperationsFiltersTests(TestCase):
    """Valida scoping, filtros avanzados y exportaciones de operaciones."""

    def test_operation_uses_logged_user_employee_profile(self):
        """Al crear operacion, se debe priorizar el perfil del usuario logueado."""
        manager_user = User.objects.create_user(email='manager@example.com', password='testpass123', role='gerente')
        manager_employee = Employee.objects.create(full_name='Manager Perfil', role='gerente', is_active=True, user=manager_user)
        self.client.force_login(manager_user)

        response = self.client.post(
            '/dashboard/operations/',
            {
                'kind': 'income',
                'category': 'service',
                'amount': '95',
                'occurred_on': '2026-04-11',
                'description': 'Operacion manager',
            },
        )

        self.assertEqual(response.status_code, 302)
        operation = FinancialOperation.objects.get(description='Operacion manager')
        self.assertEqual(operation.employee, manager_employee)

    def test_operation_ignores_manual_employee_from_post(self):
        """El backend debe ignorar employee enviado manualmente por seguridad."""
        employee_user = User.objects.create_user(email='emp@example.com', password='testpass123', role='empleado')
        logged_employee = Employee.objects.create(full_name='Empleado Logueado', role='empleado', is_active=True, user=employee_user)
        other_employee = Employee.objects.create(full_name='Otro Empleado', role='empleado', is_active=True)
        self.client.force_login(employee_user)

        response = self.client.post(
            '/dashboard/operations/',
            {
                'kind': 'income',
                'category': 'service',
                'amount': '70',
                'occurred_on': '2026-04-11',
                'description': 'Operacion segura',
                'employee': str(other_employee.id),
            },
        )

        self.assertEqual(response.status_code, 302)
        operation = FinancialOperation.objects.get(description='Operacion segura')
        self.assertEqual(operation.employee, logged_employee)

    def test_operations_advanced_filters(self):
        """Los filtros combinados deben devolver solo operaciones coincidentes."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        employee = Employee.objects.create(full_name='Ana Ruiz', role='gerente', is_active=True)
        self.client.force_login(user)

        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=100,
            occurred_on=localdate(),
            description='Corte premium',
            created_by=user,
            employee=employee,
        )
        FinancialOperation.objects.create(
            kind='expense',
            category='other',
            amount=20,
            occurred_on=localdate(),
            description='Insumos',
            created_by=user,
        )

        response = self.client.get(
            '/dashboard/operations/',
            {
                'kind': 'income',
                'category': 'service',
                'employee': str(employee.id),
                'min_amount': '50',
                'max_amount': '150',
                'q': 'premium',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Corte premium')
        self.assertNotContains(response, 'Insumos')

    def test_operations_are_paginated(self):
        """El listado de operaciones debe paginar cuando supera el limite."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(user)

        for index in range(12):
            FinancialOperation.objects.create(
                kind='income',
                category='service',
                amount=10 + index,
                occurred_on=localdate(),
                description=f'Operacion {index + 1}',
                created_by=user,
            )

        response = self.client.get('/dashboard/operations/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_next())

    def test_operations_csv_export(self):
        """La exportacion CSV debe responder con cabeceras y contenido esperados."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(user)
        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=100,
            occurred_on=localdate(),
            description='Corte premium',
            created_by=user,
        )

        response = self.client.get('/dashboard/operations/export.csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('operaciones_peluqueria_estilo.csv', response['Content-Disposition'])
        self.assertIn('Corte premium', response.content.decode())

    def test_operations_xlsx_export(self):
        """La exportacion XLSX debe devolver tipo MIME y nombre de archivo correctos."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(user)
        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=100,
            occurred_on=localdate(),
            description='Corte premium',
            created_by=user,
        )

        response = self.client.get('/dashboard/operations/export.xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('operaciones_peluqueria_estilo.xlsx', response['Content-Disposition'])

    def test_employee_only_sees_own_operations(self):
        """Empleado solo debe visualizar operaciones creadas por su usuario."""
        employee_user = User.objects.create_user(email='emp@example.com', password='testpass123', role='empleado')
        other_user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(employee_user)

        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=80,
            occurred_on=localdate(),
            description='Operacion propia',
            created_by=employee_user,
        )
        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=120,
            occurred_on=localdate(),
            description='Operacion ajena',
            created_by=other_user,
        )

        response = self.client.get('/dashboard/operations/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operacion propia')
        self.assertNotContains(response, 'Operacion ajena')

    def test_employee_csv_export_is_scoped(self):
        """La exportacion CSV del empleado debe excluir operaciones ajenas."""
        employee_user = User.objects.create_user(email='emp@example.com', password='testpass123', role='empleado')
        other_user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(employee_user)

        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=80,
            occurred_on=localdate(),
            description='Operacion propia',
            created_by=employee_user,
        )
        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=120,
            occurred_on=localdate(),
            description='Operacion ajena',
            created_by=other_user,
        )

        response = self.client.get('/dashboard/operations/export.csv')
        self.assertEqual(response.status_code, 200)
        csv_content = response.content.decode()
        self.assertIn('Operacion propia', csv_content)
        self.assertNotIn('Operacion ajena', csv_content)

    def test_employee_xlsx_export_is_scoped(self):
        """La exportacion XLSX del empleado no debe romper reglas de alcance."""
        employee_user = User.objects.create_user(email='emp@example.com', password='testpass123', role='empleado')
        other_user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(employee_user)

        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=80,
            occurred_on=localdate(),
            description='Operacion propia',
            created_by=employee_user,
        )
        FinancialOperation.objects.create(
            kind='income',
            category='service',
            amount=120,
            occurred_on=localdate(),
            description='Operacion ajena',
            created_by=other_user,
        )

        response = self.client.get('/dashboard/operations/export.xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertIn('operaciones_peluqueria_estilo.xlsx', response['Content-Disposition'])


class DashboardRoleScopeTests(TestCase):
    """Verifica datos sensibles ocultos cuando el rol es empleado."""

    def test_employee_dashboard_hides_admin_counts_and_audit(self):
        """El contexto del dashboard de empleado debe omitir metricas administrativas."""
        employee_user = User.objects.create_user(email='emp@example.com', password='testpass123', role='empleado')
        self.client.force_login(employee_user)

        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employees_count'], 0)
        self.assertFalse(response.context['can_view_audit'])


class ActivityLogTests(TestCase):
    """Asegura que las acciones relevantes generen eventos de auditoria."""

    def test_activity_log_created_for_employee_actions(self):
        """Crear empleados debe registrar evento create en ActivityLog."""
        user = User.objects.create_user(email='manager@example.com', password='testpass123', role='gerente')
        self.client.force_login(user)

        response = self.client.post(
            '/dashboard/employees/',
            {
                'full_name': 'Maria Lopez',
                'role': 'empleado',
                'phone': '999555444',
                'hired_at': '2026-04-01',
            },
        )
        self.assertEqual(response.status_code, 302)
        log = ActivityLog.objects.filter(entity_type='employee', action='create').first()
        self.assertIsNotNone(log)
        self.assertIsNotNone(log.employee)
        self.assertIsNone(log.operation)

    def test_activity_log_created_for_operation_actions(self):
        """Crear operaciones debe registrar evento create en ActivityLog."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(user)

        response = self.client.post(
            '/dashboard/operations/',
            {
                'kind': 'income',
                'category': 'service',
                'amount': '75',
                'occurred_on': '2026-04-11',
                'description': 'Corte y peinado',
            },
        )
        self.assertEqual(response.status_code, 302)
        log = ActivityLog.objects.filter(entity_type='operation', action='create').first()
        self.assertIsNotNone(log)
        self.assertIsNotNone(log.operation)
        self.assertIsNone(log.employee)


class EmployeePaginationTests(TestCase):
    """Valida que el listado de empleados use paginacion configurada."""

    def test_employees_are_paginated(self):
        """Con suficientes registros, la vista de empleados debe tener pagina siguiente."""
        user = User.objects.create_user(email='manager@example.com', password='testpass123', role='gerente')
        self.client.force_login(user)

        for index in range(7):
            Employee.objects.create(full_name=f'Empleado {index + 1}', role='empleado')

        response = self.client.get('/dashboard/employees/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_next())


class SalesFlowTests(TestCase):
    """Pruebas de ventas con multiples items y actualizacion de inventario."""

    def test_sales_create_with_multiple_products_and_service(self):
        """Una venta puede incluir varios productos/servicios y descuenta stock."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', role='admin')
        self.client.force_login(user)

        shampoo = Product.objects.create(name='Shampoo', sku='SH-001', unit_price=20, stock=8)
        wax = Product.objects.create(name='Cera', sku='WX-001', unit_price=15, stock=5)
        cut = Service.objects.create(name='Corte clasico', price=30)

        response = self.client.post(
            '/dashboard/sales/',
            {
                'occurred_on': '2026-04-13',
                'notes': 'Venta mostrador',
                'item_type[]': ['product', 'product', 'service'],
                'item_ref[]': [str(shampoo.id), str(wax.id), str(cut.id)],
                'item_qty[]': ['2', '1', '1'],
            },
        )

        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.first()
        self.assertIsNotNone(sale)
        self.assertEqual(sale.items.count(), 3)
        self.assertEqual(sale.total_amount, 85)

        shampoo.refresh_from_db()
        wax.refresh_from_db()
        self.assertEqual(shampoo.stock, 6)
        self.assertEqual(wax.stock, 4)

        operation = FinancialOperation.objects.filter(description__icontains=f'Venta #{sale.id}').first()
        self.assertIsNotNone(operation)
        self.assertEqual(operation.kind, 'income')
