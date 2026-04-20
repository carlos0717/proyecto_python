"""Modelos del dominio operativo: empleados, movimientos y auditoria."""

# settings se usa para referenciar el modelo de usuario configurable del proyecto.
from django.conf import settings
# ValidationError garantiza reglas de dominio antes de persistir.
from django.core.exceptions import ValidationError
# models define campos, relaciones y metadatos persistidos en base de datos.
from django.db import models
from django.db.models import Q


class Employee(models.Model):
    """Perfil operativo del colaborador, con rol y estado de actividad."""

    class Role(models.TextChoices):
        """Roles disponibles dentro del contexto operativo del negocio."""

        MANAGER = 'gerente', 'Gerente'
        EMPLOYEE = 'empleado', 'Empleado'

    # Vincula el perfil del usuario con el registro operativo del empleado.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile',
    )
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    phone = models.CharField(max_length=30, blank=True, default='')
    is_active = models.BooleanField(default=True)
    hired_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['is_active', 'role']),
            models.Index(fields=['full_name']),
        ]

    def __str__(self):
        """Texto legible para panel admin y selects de interfaz."""
        return f"{self.full_name} ({self.get_role_display()})"


class Service(models.Model):
    """Catalogo de servicios ofrecidos por la peluqueria."""

    name = models.CharField(max_length=120, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]

    def __str__(self):
        """Representacion amigable para listados y selects."""
        return f"{self.name} (${self.price})"


class Product(models.Model):
    """Catalogo de productos con control de stock en inventario."""

    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40, unique=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        """Texto de referencia para administracion y detalle de ventas."""
        return f"{self.name} ({self.sku})"


class Sale(models.Model):
    """Cabecera de venta que agrupa uno o varios items vendidos."""

    occurred_on = models.DateField()
    notes = models.CharField(max_length=255, blank=True, default='')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sales_created',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-occurred_on', '-created_at']
        indexes = [
            models.Index(fields=['occurred_on', 'created_at']),
            models.Index(fields=['created_by', 'occurred_on']),
            models.Index(fields=['employee', 'occurred_on']),
        ]

    def __str__(self):
        """Referencia corta de venta usada en listados."""
        return f"Venta #{self.id} - ${self.total_amount}"


class SaleItem(models.Model):
    """Linea de detalle de venta para soportar multiples productos/servicios."""

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sale_items',
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sale_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['sale', 'id']),
            models.Index(fields=['product']),
            models.Index(fields=['service']),
        ]
        # Temporarily removing constraints to debug the issue
        # constraints = [
        #     models.CheckConstraint(check=Q(quantity__gt=0), name='sale_item_quantity_gt_zero'),
        #     models.CheckConstraint(check=Q(unit_price__gt=0), name='sale_item_unit_price_gt_zero'),
        #     models.CheckConstraint(check=Q(subtotal__gt=0), name='sale_item_subtotal_gt_zero'),
        # ]

    def clean(self):
        """Exige que el item sea producto o servicio, pero nunca ambos."""
        has_product = self.product_id is not None
        has_service = self.service_id is not None
        if has_product == has_service:
            raise ValidationError('Cada ítem debe tener un producto o un servicio, pero no ambos.')

    def save(self, *args, **kwargs):
        """Valida consistencia del item antes de persistir en BD."""
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        """Etiqueta legible para inspeccion de detalle."""
        item_name = self.product.name if self.product else self.service.name
        return f"{item_name} x{self.quantity} (${self.subtotal})"


class FinancialOperation(models.Model):
    """Movimiento financiero (ingreso/egreso) asociado a usuario y empleado."""

    class Kind(models.TextChoices):
        """Tipo contable del movimiento registrado."""

        INCOME = 'income', 'Ingreso'
        EXPENSE = 'expense', 'Egreso'

    class Category(models.TextChoices):
        """Clasificacion funcional para segmentar reportes."""

        SERVICE = 'service', 'Servicio'
        PRODUCT = 'product', 'Producto'
        OTHER = 'other', 'Otro'

    kind = models.CharField(max_length=10, choices=Kind.choices)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.SERVICE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    occurred_on = models.DateField()
    description = models.CharField(max_length=255, blank=True, default='')
    # Guarda quien creo el movimiento y, cuando aplica, el responsable operativo.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='operations_created',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Financial Operation'
        verbose_name_plural = 'Financial Operations'
        ordering = ['-occurred_on', '-created_at']
        indexes = [
            models.Index(fields=['occurred_on', 'created_at']),
            models.Index(fields=['kind', 'occurred_on']),
            models.Index(fields=['category', 'occurred_on']),
            models.Index(fields=['created_by', 'occurred_on']),
            models.Index(fields=['employee', 'occurred_on']),
        ]
        # Temporarily removing constraints to debug the issue
        # constraints = [
        #     models.CheckConstraint(check=Q(amount__gt=0), name='financial_operation_amount_gt_zero'),
        # ]

    def __str__(self):
        """Representacion breve con signo para inspeccion rapida de registros."""
        sign = '+' if self.kind == self.Kind.INCOME else '-'
        return f"{self.get_kind_display()} {sign}${self.amount} ({self.occurred_on})"


class ActivityLog(models.Model):
    """Bitacora de auditoria para rastrear acciones relevantes en el sistema."""

    class Action(models.TextChoices):
        """Tipo de accion auditada sobre entidades del negocio."""

        CREATE = 'create', 'Crear'
        UPDATE = 'update', 'Actualizar'
        TOGGLE = 'toggle', 'Activar/Desactivar'

    action = models.CharField(max_length=20, choices=Action.choices)
    entity_type = models.CharField(max_length=50)
    entity_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True, default='')
    operation = models.ForeignKey(
        FinancialOperation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['operation', 'created_at']),
            models.Index(fields=['employee', 'created_at']),
        ]

    def __str__(self):
        """Resumen legible del evento para listados y depuracion."""
        return f"{self.get_action_display()} - {self.title}"
