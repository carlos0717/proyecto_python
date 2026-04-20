"""Vistas del dashboard: operaciones, empleados, catalogos, ventas y reportes."""

import csv
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.timezone import localdate
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook

from .models import (
    ActivityLog,
    Employee,
    FinancialOperation,
    Product,
    Sale,
    SaleItem,
    Service,
)


def _can_access_business_modules(user):
    """Permite modulos operativos a colaboradores y a roles de gestion."""
    if not user.is_authenticated:
        return False
    return user.user_type == 'colaborador' or user.role in {'admin', 'gerente'}


def _can_manage_employees(user):
    """Retorna si el usuario puede crear/editar personal del negocio."""
    return user.is_authenticated and user.role in {'admin', 'gerente'}


def _can_view_all_operations(user):
    """Retorna si el usuario puede consultar operaciones de todo el equipo."""
    return user.is_authenticated and user.role in {'admin', 'gerente'}


def _can_view_audit(user):
    """Retorna si el usuario puede acceder a bitacora completa de auditoria."""
    return user.is_authenticated and user.role in {'admin', 'gerente'}


def _parse_period_dates(request):
    """Obtiene rango de fechas desde query params o aplica valores por defecto."""
    today = localdate()
    start_date = parse_date(request.GET.get('start', ''))
    end_date = parse_date(request.GET.get('end', ''))

    if not start_date:
        start_date = today.replace(day=1)
    if not end_date:
        end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date


def _sum_amount(queryset):
    """Suma montos del queryset y devuelve 0.00 cuando no hay resultados."""
    return queryset.aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']


def _parse_decimal(value):
    """Convierte string a Decimal y retorna None si el valor no es valido."""
    if value in {None, ''}:
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def _apply_operation_filters(request, queryset):
    """Aplica filtros de busqueda y orden a operaciones segun parametros GET."""
    kind_filter = request.GET.get('kind', '')
    category_filter = request.GET.get('category', '')
    employee_filter = request.GET.get('employee', '')
    query_filter = request.GET.get('q', '').strip()
    min_amount = _parse_decimal(request.GET.get('min_amount', ''))
    max_amount = _parse_decimal(request.GET.get('max_amount', ''))
    sort_filter = request.GET.get('sort', 'date_desc')

    valid_kinds = {choice[0] for choice in FinancialOperation.Kind.choices}
    valid_categories = {choice[0] for choice in FinancialOperation.Category.choices}
    valid_sorts = {
        'date_desc': '-occurred_on',
        'date_asc': 'occurred_on',
        'amount_desc': '-amount',
        'amount_asc': 'amount',
    }

    if kind_filter in valid_kinds:
        queryset = queryset.filter(kind=kind_filter)
    if category_filter in valid_categories:
        queryset = queryset.filter(category=category_filter)
    if employee_filter.isdigit():
        queryset = queryset.filter(employee_id=int(employee_filter))
    if query_filter:
        queryset = queryset.filter(description__icontains=query_filter)
    if min_amount is not None:
        queryset = queryset.filter(amount__gte=min_amount)
    if max_amount is not None:
        queryset = queryset.filter(amount__lte=max_amount)

    queryset = queryset.order_by(valid_sorts.get(sort_filter, '-occurred_on'), '-created_at')

    return queryset, {
        'selected_kind': kind_filter,
        'selected_category': category_filter,
        'selected_employee': employee_filter,
        'query_filter': query_filter,
        'min_amount': request.GET.get('min_amount', ''),
        'max_amount': request.GET.get('max_amount', ''),
        'selected_sort': sort_filter,
    }


def _build_operation_base_queryset(start_date, end_date):
    """Construye queryset base optimizado para listar operaciones por periodo."""
    return FinancialOperation.objects.select_related('employee', 'created_by').filter(
        occurred_on__range=(start_date, end_date),
    )


def _scope_operations_for_user(user, queryset):
    """Restringe datos para empleados y permite vista global a roles de gestion."""
    if _can_view_all_operations(user):
        return queryset
    return queryset.filter(created_by=user)


def _employee_for_logged_user(user):
    """Obtiene el perfil Employee activo vinculado al usuario autenticado."""
    if not user.is_authenticated:
        return None
    return Employee.objects.filter(user=user, is_active=True).first()


def _log_activity(*, action, title, details='', performed_by=None, operation=None, employee=None, entity_type='', entity_id=None):
    """Centraliza la auditoria con relacion FK directa y fallback de entidad textual."""
    if operation is not None:
        resolved_entity_type = 'operation'
        resolved_entity_id = operation.id
    elif employee is not None:
        resolved_entity_type = 'employee'
        resolved_entity_id = employee.id
    else:
        resolved_entity_type = entity_type
        resolved_entity_id = entity_id or 0

    ActivityLog.objects.create(
        action=action,
        entity_type=resolved_entity_type,
        entity_id=resolved_entity_id,
        title=title,
        details=details,
        operation=operation,
        employee=employee,
        performed_by=performed_by,
    )


def _deny_client_access(request, message='Esta seccion es solo para colaboradores.'):
    """Bloquea acceso de clientes a modulos operativos internos."""
    if _can_access_business_modules(request.user):
        return None
    messages.error(request, message)
    return redirect('dashboard:home')


def _parse_sale_items_from_request(request):
    """Valida y normaliza items para venta con multiples lineas."""
    item_types = request.POST.getlist('item_type[]')
    item_refs = request.POST.getlist('item_ref[]')
    item_qty = request.POST.getlist('item_qty[]')

    if not item_types or len(item_types) != len(item_refs) or len(item_refs) != len(item_qty):
        return None, 'Debes enviar al menos un item valido para la venta.'

    parsed_items = []
    for idx, item_type in enumerate(item_types):
        ref_value = item_refs[idx].strip()
        qty_value = item_qty[idx].strip()

        if not ref_value or not qty_value:
            continue
        if item_type not in {'product', 'service'}:
            return None, 'Tipo de item invalido en la venta.'
        if not qty_value.isdigit() or int(qty_value) <= 0:
            return None, 'Cada item debe tener cantidad mayor a cero.'

        parsed_items.append(
            {
                'item_type': item_type,
                'ref_id': int(ref_value),
                'quantity': int(qty_value),
            }
        )

    if not parsed_items:
        return None, 'Debes agregar al menos un producto o servicio en la venta.'

    return parsed_items, ''


@login_required
@require_http_methods(['GET'])
def dashboard_home(request):
    """Renderiza metricas clave del dia/mes y actividad reciente del dashboard."""
    today = localdate()
    month_start = today.replace(day=1)

    day_operations = _scope_operations_for_user(request.user, FinancialOperation.objects.filter(occurred_on=today))
    month_operations = _scope_operations_for_user(request.user, FinancialOperation.objects.filter(occurred_on__range=(month_start, today)))

    day_income = _sum_amount(day_operations.filter(kind=FinancialOperation.Kind.INCOME))
    day_expense = _sum_amount(day_operations.filter(kind=FinancialOperation.Kind.EXPENSE))
    month_income = _sum_amount(month_operations.filter(kind=FinancialOperation.Kind.INCOME))
    month_expense = _sum_amount(month_operations.filter(kind=FinancialOperation.Kind.EXPENSE))

    context = {
        'day_income': day_income,
        'day_expense': day_expense,
        'day_balance': day_income - day_expense,
        'month_income': month_income,
        'month_expense': month_expense,
        'month_balance': month_income - month_expense,
        'employees_count': Employee.objects.filter(is_active=True).count() if _can_manage_employees(request.user) else 0,
        'recent_operations': _scope_operations_for_user(
            request.user,
            FinancialOperation.objects.select_related('employee').order_by('-occurred_on', '-created_at'),
        )[:8],
        'recent_activity': ActivityLog.objects.select_related('performed_by')[:6] if _can_view_audit(request.user) else ActivityLog.objects.select_related('performed_by').filter(performed_by=request.user)[:6],
        'can_manage_employees': _can_manage_employees(request.user),
        'can_view_audit': _can_view_audit(request.user),
        'can_access_business': _can_access_business_modules(request.user),
    }
    return render(request, 'dashboard/home.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    """Permite al usuario actualizar sus datos basicos de perfil."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save(update_fields=['first_name', 'last_name'])
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('dashboard:profile')
    return render(request, 'dashboard/profile.html')


@login_required
@require_http_methods(['GET', 'POST'])
def operations(request):
    """Gestiona alta y listado filtrable de operaciones financieras."""
    forbidden_response = _deny_client_access(request)
    if forbidden_response:
        return forbidden_response

    start_date, end_date = _parse_period_dates(request)

    if request.method == 'POST':
        kind = request.POST.get('kind', FinancialOperation.Kind.INCOME)
        category = request.POST.get('category', FinancialOperation.Category.SERVICE)
        description = request.POST.get('description', '').strip()
        occurred_on = parse_date(request.POST.get('occurred_on', '')) or localdate()

        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except Exception:
            messages.error(request, 'Monto invalido.')
            return redirect('dashboard:operations')

        if amount <= 0:
            messages.error(request, 'El monto debe ser mayor que 0.')
            return redirect('dashboard:operations')

        employee = _employee_for_logged_user(request.user)

        operation = FinancialOperation.objects.create(
            kind=kind,
            category=category,
            amount=amount,
            description=description,
            occurred_on=occurred_on,
            employee=employee,
            created_by=request.user,
        )

        _log_activity(
            action=ActivityLog.Action.CREATE,
            title=f'Operacion creada: {kind} / {category}',
            details=description,
            performed_by=request.user,
            operation=operation,
        )

        messages.success(request, 'Operacion registrada correctamente.')
        return redirect('dashboard:operations')

    operations_qs, filter_context = _apply_operation_filters(
        request,
        _build_operation_base_queryset(start_date, end_date),
    )
    operations_qs = _scope_operations_for_user(request.user, operations_qs)

    paginator = Paginator(operations_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'operations': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'employees': Employee.objects.filter(is_active=True),
        'start_date': start_date,
        'end_date': end_date,
        'total_income': _sum_amount(operations_qs.filter(kind=FinancialOperation.Kind.INCOME)),
        'total_expense': _sum_amount(operations_qs.filter(kind=FinancialOperation.Kind.EXPENSE)),
        'can_view_all_operations': _can_view_all_operations(request.user),
    }
    context.update(filter_context)
    context['balance'] = context['total_income'] - context['total_expense']
    return render(request, 'dashboard/operations.html', context)


@login_required
@require_http_methods(['GET'])
def operations_export_csv(request):
    """Exporta operaciones filtradas a CSV para analisis externo."""
    forbidden_response = _deny_client_access(request)
    if forbidden_response:
        return forbidden_response

    start_date, end_date = _parse_period_dates(request)
    operations_qs, _ = _apply_operation_filters(request, _build_operation_base_queryset(start_date, end_date))
    operations_qs = _scope_operations_for_user(request.user, operations_qs)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="operaciones_peluqueria_estilo.csv"'

    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Tipo', 'Categoria', 'Monto', 'Empleado', 'Descripcion', 'Creado por'])
    for operation in operations_qs:
        writer.writerow([
            operation.occurred_on,
            operation.get_kind_display(),
            operation.get_category_display(),
            operation.amount,
            operation.employee.full_name if operation.employee else '',
            operation.description,
            operation.created_by.email,
        ])

    return response


@login_required
@require_http_methods(['GET'])
def operations_export_xlsx(request):
    """Exporta operaciones filtradas a XLSX para consumo en Excel."""
    forbidden_response = _deny_client_access(request)
    if forbidden_response:
        return forbidden_response

    start_date, end_date = _parse_period_dates(request)
    operations_qs, _ = _apply_operation_filters(request, _build_operation_base_queryset(start_date, end_date))
    operations_qs = _scope_operations_for_user(request.user, operations_qs)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Operaciones'

    headers = ['Fecha', 'Tipo', 'Categoria', 'Monto', 'Empleado', 'Descripcion', 'Creado por']
    sheet.append(headers)
    for operation in operations_qs:
        sheet.append([
            str(operation.occurred_on),
            operation.get_kind_display(),
            operation.get_category_display(),
            float(operation.amount),
            operation.employee.full_name if operation.employee else '',
            operation.description,
            operation.created_by.email,
        ])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="operaciones_peluqueria_estilo.xlsx"'
    return response


@login_required
@require_http_methods(['GET', 'POST'])
def employees(request):
    """Lista empleados y permite crear nuevos registros de personal."""
    if not _can_manage_employees(request.user):
        messages.error(request, 'No tienes permisos para gestionar empleados.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        role = request.POST.get('role', Employee.Role.EMPLOYEE)
        phone = request.POST.get('phone', '').strip()
        hired_at = parse_date(request.POST.get('hired_at', ''))

        if not full_name:
            messages.error(request, 'El nombre del empleado es obligatorio.')
            return redirect('dashboard:employees')

        employee = Employee.objects.create(
            full_name=full_name,
            role=role,
            phone=phone,
            hired_at=hired_at,
            is_active=True,
        )
        _log_activity(
            action=ActivityLog.Action.CREATE,
            title=f'Empleado creado: {employee.full_name}',
            details=f'Rol: {employee.get_role_display()}',
            performed_by=request.user,
            employee=employee,
        )
        messages.success(request, 'Empleado registrado correctamente.')
        return redirect('dashboard:employees')

    employees_qs = Employee.objects.select_related('user').order_by('-is_active', 'full_name')
    paginator = Paginator(employees_qs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'employees': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'active_count': Employee.objects.filter(is_active=True).count(),
    }
    return render(request, 'dashboard/employees.html', context)


@login_required
@require_http_methods(['POST'])
def employee_update(request, employee_id):
    """Actualiza datos de un empleado existente con validaciones basicas."""
    if not _can_manage_employees(request.user):
        messages.error(request, 'No tienes permisos para editar empleados.')
        return redirect('dashboard:home')

    employee = get_object_or_404(Employee, id=employee_id)
    full_name = request.POST.get('full_name', '').strip()
    role = request.POST.get('role', Employee.Role.EMPLOYEE)
    phone = request.POST.get('phone', '').strip()
    hired_at = parse_date(request.POST.get('hired_at', ''))

    if not full_name:
        messages.error(request, 'El nombre del empleado es obligatorio.')
        return redirect('dashboard:employees')

    employee.full_name = full_name
    employee.role = role if role in {choice[0] for choice in Employee.Role.choices} else Employee.Role.EMPLOYEE
    employee.phone = phone
    employee.hired_at = hired_at
    employee.save(update_fields=['full_name', 'role', 'phone', 'hired_at', 'updated_at'])

    _log_activity(
        action=ActivityLog.Action.UPDATE,
        title=f'Empleado actualizado: {employee.full_name}',
        details=f'Rol: {employee.get_role_display()} | Telefono: {employee.phone}',
        performed_by=request.user,
        employee=employee,
    )

    messages.success(request, f'Empleado {employee.full_name} actualizado.')
    return redirect('dashboard:employees')


@login_required
@require_http_methods(['POST'])
def employee_toggle_active(request, employee_id):
    """Activa o desactiva un empleado para controlar su vigencia operativa."""
    if not _can_manage_employees(request.user):
        messages.error(request, 'No tienes permisos para desactivar empleados.')
        return redirect('dashboard:home')

    employee = get_object_or_404(Employee, id=employee_id)
    employee.is_active = not employee.is_active
    employee.save(update_fields=['is_active', 'updated_at'])

    action_label = 'activado' if employee.is_active else 'desactivado'

    _log_activity(
        action=ActivityLog.Action.TOGGLE,
        title=f'Empleado {action_label}: {employee.full_name}',
        details=f'Nuevo estado: {"Activo" if employee.is_active else "Inactivo"}',
        performed_by=request.user,
        employee=employee,
    )

    messages.success(request, f'Empleado {employee.full_name} {action_label} correctamente.')
    return redirect('dashboard:employees')


@login_required
@require_http_methods(['GET', 'POST'])
def catalog(request):
    """Gestiona catalogos de servicios y productos con stock."""
    forbidden_response = _deny_client_access(request)
    if forbidden_response:
        return forbidden_response

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'create_service':
            name = request.POST.get('service_name', '').strip()
            price = _parse_decimal(request.POST.get('service_price', ''))
            if not name or price is None or price <= 0:
                messages.error(request, 'Servicio invalido. Verifica nombre y precio.')
                return redirect('dashboard:catalog')
            Service.objects.create(name=name, price=price)
            messages.success(request, 'Servicio registrado correctamente.')
            return redirect('dashboard:catalog')

        if action == 'create_product':
            name = request.POST.get('product_name', '').strip()
            sku = request.POST.get('product_sku', '').strip().upper()
            price = _parse_decimal(request.POST.get('product_price', ''))
            stock = request.POST.get('product_stock', '0').strip()

            if not name or not sku or price is None or price <= 0 or not stock.isdigit():
                messages.error(request, 'Producto invalido. Verifica datos y stock.')
                return redirect('dashboard:catalog')

            Product.objects.create(name=name, sku=sku, unit_price=price, stock=int(stock))
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('dashboard:catalog')

        if action == 'adjust_stock':
            product_id = request.POST.get('product_id', '')
            stock = request.POST.get('new_stock', '').strip()
            if not product_id.isdigit() or not stock.isdigit():
                messages.error(request, 'Ajuste de stock invalido.')
                return redirect('dashboard:catalog')
            product = get_object_or_404(Product, id=int(product_id))
            product.stock = int(stock)
            product.save(update_fields=['stock', 'updated_at'])
            messages.success(request, f'Stock actualizado para {product.name}.')
            return redirect('dashboard:catalog')

        messages.error(request, 'Accion de catalogo no reconocida.')
        return redirect('dashboard:catalog')

    context = {
        'services': Service.objects.order_by('name'),
        'products': Product.objects.order_by('name'),
    }
    return render(request, 'dashboard/catalog.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def sales(request):
    """Registra ventas con detalle multiproducto/multiservicio y actualiza inventario."""
    forbidden_response = _deny_client_access(request)
    if forbidden_response:
        return forbidden_response

    start_date, end_date = _parse_period_dates(request)

    if request.method == 'POST':
        occurred_on = parse_date(request.POST.get('occurred_on', '')) or localdate()
        notes = request.POST.get('notes', '').strip()
        items_data, error_msg = _parse_sale_items_from_request(request)

        if error_msg:
            messages.error(request, error_msg)
            return redirect('dashboard:sales')

        employee = _employee_for_logged_user(request.user)
        if employee is None and request.POST.get('employee_id', '').isdigit() and _can_manage_employees(request.user):
            employee = Employee.objects.filter(id=int(request.POST['employee_id']), is_active=True).first()

        try:
            with transaction.atomic():
                sale = Sale.objects.create(
                    occurred_on=occurred_on,
                    notes=notes,
                    created_by=request.user,
                    employee=employee,
                )

                total = Decimal('0.00')
                has_product = False

                for item_data in items_data:
                    quantity = item_data['quantity']

                    if item_data['item_type'] == 'product':
                        product = get_object_or_404(Product, id=item_data['ref_id'], is_active=True)
                        if product.stock < quantity:
                            raise ValueError(f'Stock insuficiente para {product.name}. Disponible: {product.stock}.')
                        unit_price = product.unit_price
                        subtotal = unit_price * quantity
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            unit_price=unit_price,
                            subtotal=subtotal,
                        )
                        product.stock -= quantity
                        product.save(update_fields=['stock', 'updated_at'])
                        has_product = True
                    else:
                        service = get_object_or_404(Service, id=item_data['ref_id'], is_active=True)
                        unit_price = service.price
                        subtotal = unit_price * quantity
                        SaleItem.objects.create(
                            sale=sale,
                            service=service,
                            quantity=quantity,
                            unit_price=unit_price,
                            subtotal=subtotal,
                        )

                    total += subtotal

                sale.total_amount = total
                sale.save(update_fields=['total_amount', 'updated_at'])

                operation = FinancialOperation.objects.create(
                    kind=FinancialOperation.Kind.INCOME,
                    category=FinancialOperation.Category.PRODUCT if has_product else FinancialOperation.Category.SERVICE,
                    amount=total,
                    occurred_on=occurred_on,
                    description=f'Venta #{sale.id} - {notes[:120]}',
                    employee=employee,
                    created_by=request.user,
                )

                _log_activity(
                    action=ActivityLog.Action.CREATE,
                    title=f'Venta registrada #{sale.id}',
                    details=f'Items: {sale.items.count()} | Total: {sale.total_amount}',
                    performed_by=request.user,
                    operation=operation,
                    entity_type='sale',
                    entity_id=sale.id,
                )

        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('dashboard:sales')

        messages.success(request, f'Venta #{sale.id} registrada por {sale.total_amount}.')
        return redirect('dashboard:sales')

    sales_qs = Sale.objects.select_related('employee', 'created_by').prefetch_related('items__product', 'items__service').filter(
        occurred_on__range=(start_date, end_date)
    )

    if not _can_view_all_operations(request.user):
        sales_qs = sales_qs.filter(created_by=request.user)

    paginator = Paginator(sales_qs, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'sales': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'start_date': start_date,
        'end_date': end_date,
        'services': Service.objects.filter(is_active=True).order_by('name'),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'employees': Employee.objects.filter(is_active=True).order_by('full_name'),
    }
    return render(request, 'dashboard/sales.html', context)


@login_required
@require_http_methods(['GET'])
def reports(request):
    """Muestra reporte comparativo entre periodo actual y periodo anterior."""
    forbidden_response = _deny_client_access(request)
    if forbidden_response:
        return forbidden_response

    start_date, end_date = _parse_period_dates(request)
    last_period_start = start_date - timedelta(days=(end_date - start_date).days + 1)
    last_period_end = start_date - timedelta(days=1)

    current_ops = _scope_operations_for_user(
        request.user,
        FinancialOperation.objects.filter(occurred_on__range=(start_date, end_date)),
    )
    previous_ops = _scope_operations_for_user(
        request.user,
        FinancialOperation.objects.filter(occurred_on__range=(last_period_start, last_period_end)),
    )

    current_income = _sum_amount(current_ops.filter(kind=FinancialOperation.Kind.INCOME))
    current_expense = _sum_amount(current_ops.filter(kind=FinancialOperation.Kind.EXPENSE))
    previous_income = _sum_amount(previous_ops.filter(kind=FinancialOperation.Kind.INCOME))
    previous_expense = _sum_amount(previous_ops.filter(kind=FinancialOperation.Kind.EXPENSE))

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'income': current_income,
        'expense': current_expense,
        'balance': current_income - current_expense,
        'previous_income': previous_income,
        'previous_expense': previous_expense,
        'operations': current_ops.select_related('employee')[:20],
    }
    return render(request, 'dashboard/reports.html', context)
