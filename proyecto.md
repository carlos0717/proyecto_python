# Documentación Completa del Sistema SaaS Django - Plataforma de Gestión Empresarial

## Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Base de Datos - Modelo Entidad Relación](#base-de-datos---modelo-entidad-relación)
5. [Componentes Principales](#componentes-principales)
6. [Explicación de Archivos Clave](#explicación-de-archivos-clave)
7. [Roles y Permisos](#roles-y-permisos)
8. [Flujo de Datos](#flujo-de-datos)
9. [Características Principales](#características-principales)

---

## Visión General

Este es un **SaaS (Software as a Service) empresarial** construido con Django 6.0, diseñado para gestionar operaciones financieras, empleados y reportes de pequeños negocios (principalmente salones de belleza/estética).

### ¿Para qué sirve?
- **Control diario de ingresos y egresos**: Registra operaciones financieras por servicio o producto
- **Gestión de empleados**: Administra personal, roles y estado laboral
- **Reportes y análisis**: Visualiza resultados diarios y mensuales con estadísticas
- **Autenticación de usuario**: Sistema seguro basado en email
- **Suscripciones con Stripe**: Modelo de negocio SaaS con planes pagos

### ¿Por qué esta arquitectura?
- **Django**: Framework robusto, seguro y escalable para aplicaciones web
- **Email-only authentication**: Simplificar el registro (sin usuarios/contraseñas complejos)
- **Roles y permisos**: Control granular de acceso (Admin, Gerente, Empleado)
- **SaaS patterns**: Base para monetización con Stripe
- **Aplicaciones modulares**: Separación de responsabilidades por dominio

---

## Stack Tecnológico

### Backend
- **Framework**: Django 6.0 (Python 3.12)
- **Autenticación**: django-allauth (solo email, sin username)
- **Pagos**: Stripe (Payment Methods API)
- **ORM**: Django ORM (SQLite desarrollo / PostgreSQL producción)
- **Tareas asincrónicas**: Django 6.0 native `@task()` decorator
- **Servidor**: Gunicorn
- **Static files**: WhiteNoise

### Frontend
- **Estilos**: Tailwind CSS (CDN)
- **Interactividad**: Alpine.js + HTMX
- **Templates**: Django templates (Jinja2)

### Base de Datos
- **Desarrollo**: SQLite
- **Producción**: PostgreSQL (via `DATABASE_URL`)

### Herramientas
- **Linting**: Ruff
- **Control de versión**: Git

---

## Estructura del Proyecto

```
django-saas-boilerplate/
├── core/                    # Configuración principal de Django
│   ├── settings.py         # Variables, apps instaladas, middleware
│   ├── urls.py             # Enrutamiento principal
│   ├── wsgi.py             # Deploy con Gunicorn
│   └── asgi.py             # WebSockets/async
│
├── apps/                   # Aplicaciones del negocio
│   ├── accounts/           # Gestión de usuarios
│   │   ├── models.py       # CustomUser (email-only)
│   │   ├── forms.py        # Validación de signup/login
│   │   ├── admin.py        # Panel admin
│   │   └── migrations/     # Cambios en BD
│   │
│   ├── dashboard/          # Panel principal del usuario
│   │   ├── models.py       # Employee, FinancialOperation, ActivityLog
│   │   ├── views.py        # Lógica de vistas
│   │   ├── urls.py         # Rutas del dashboard
│   │   ├── tasks.py        # Tareas background
│   │   ├── admin.py        # Admin customizado
│   │   └── management/
│   │       └── commands/
│   │           └── seed_data.py  # Datos de prueba
│   │
│   ├── landing/            # Páginas públicas
│   │   ├── views.py        # Home, Pricing, Features
│   │   └── urls.py         # Rutas públicas
│   │
│   └── subscriptions/      # Integración con Stripe
│       ├── models.py       # StripeCustomer
│       ├── views.py        # Webhooks de Stripe
│       └── urls.py         # Endpoints de suscripción
│
├── templates/              # HTML templates
│   ├── base.html          # Base pública
│   ├── account/           # Autenticación (login, signup)
│   ├── dashboard/         # Plantillas autenticadas
│   ├── landing/           # Páginas públicas
│   └── subscriptions/     # Suscripciones
│
├── static/                # Archivos estáticos
│   └── css/
│       └── design-system.css
│
├── manage.py              # Ejecutable de Django
├── requirements.txt       # Dependencias Python
├── pyproject.toml         # Configuración Ruff
├── Makefile               # Comandos útiles
└── .env                   # Variables de entorno (gitignore)
```

---

## Base de Datos - Modelo Entidad Relación

### Diagrama ER (Entity-Relationship)

```
┌─────────────────────────────┐
│      CustomUser             │ (accounts.models)
│ (Django Auth User extendido)│
├─────────────────────────────┤
│ id (PK)                     │
│ email (UNIQUE)              │
│ password                    │
│ role (Enum)                 │
│ first_name                  │
│ last_name                   │
│ is_active                   │
│ is_staff                    │
│ is_superuser                │
│ created_at                  │
└──────────────┬──────────────┘
               │ 1:1 (OneToOne)
               │
        ┌──────▼──────────────────┐
        │  StripeCustomer         │ (subscriptions.models)
        ├─────────────────────────┤
        │ id (PK)                 │
        │ user_id (FK→CustomUser) │◄─── Usuario suscriptor
        │ stripe_customer_id      │
        │ stripe_subscription_id  │
        │ subscription_status     │
        │ created_at              │
        │ updated_at              │
        └─────────────────────────┘

┌──────────────────────────────┐
│      Employee                │ (dashboard.models)
├──────────────────────────────┤
│ id (PK)                      │
│ user_id (FK→CustomUser) 0..1 │◄─── Vinculación opcional
│ full_name                    │
│ role (Enum)                  │
│ phone                        │
│ is_active                    │
│ hired_at                     │
│ created_at                   │
│ updated_at                   │
└────────┬─────────────────────┘
         │ 1:N (OneToMany)
         │
         │     ┌──────────────────────────────┐
         │     │ FinancialOperation           │ (dashboard.models)
         │     ├──────────────────────────────┤
         │     │ id (PK)                      │
         └────►│ employee_id (FK→Employee)    │◄─── Responsable
               │ created_by_id (FK→CustomUser)│◄─── Quién la registró
               │ kind (Enum: income/expense)  │
               │ category (Enum: service/..)  │
               │ amount (Decimal)             │
               │ occurred_on (Date)           │
               │ description                  │
               │ created_at                   │
               │ updated_at                   │
               └──────────────────────────────┘

┌──────────────────────────────┐
│      ActivityLog             │ (dashboard.models)
├──────────────────────────────┤
│ id (PK)                      │
│ action (Enum: create/update) │
│ entity_type (String)         │
│ entity_id (Integer)          │
│ title                        │
│ details                      │
│ performed_by_id (FK→User)    │◄─── Quién hizo la acción
│ created_at                   │
└──────────────────────────────┘
```

### Entidades y Atributos Detallados

#### 1. **CustomUser** (accounts/models.py)
**Propósito**: Modelo personalizado de usuario que reemplaza el username con email.

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | PK | Identificador único |
| email | EmailField (UNIQUE) | Email del usuario (campo único para login) |
| password | CharField | Contraseña hasheada |
| role | CharField(choices) | ADMIN, MANAGER, EMPLOYEE |
| first_name | CharField | Nombre |
| last_name | CharField | Apellido |
| is_active | Boolean | Cuenta activa/inactiva |
| is_staff | Boolean | Puede acceder admin |
| is_superuser | Boolean | Tiene todos los permisos |
| date_joined | DateTime | Fecha de registro |

**¿Por qué?**: Simplificar login (solo email), validar formato RFC5322, permitir diferentes roles.

---

#### 2. **StripeCustomer** (subscriptions/models.py)
**Propósito**: Vincular usuario de nuestra app con cliente Stripe y su suscripción.

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | PK | ID interno |
| user_id | FK→CustomUser | Relación 1:1 con usuario |
| stripe_customer_id | CharField | ID generado por Stripe |
| stripe_subscription_id | CharField | ID de la suscripción activa |
| subscription_status | CharField | active, canceled, past_due, etc. |
| created_at | DateTime | Cuándo se creó el cliente |
| updated_at | DateTime | Última actualización |

**¿Por qué?**: Guardar referencias de Stripe localmente para sincronizar webhooks y estado.

---

#### 3. **Employee** (dashboard/models.py)
**Propósito**: Perfil operativo de empleados (complementa CustomUser).

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | PK | ID único |
| user_id | FK→CustomUser (nullable) | Vinculación opcional con usuario |
| full_name | CharField | Nombre completo |
| role | CharField(choices) | MANAGER, EMPLOYEE |
| phone | CharField | Teléfono de contacto |
| is_active | Boolean | Empleado activo/inactivo |
| hired_at | DateField | Fecha de contratación |
| created_at | DateTime | Creación del registro |
| updated_at | DateTime | Última actualización |

**¿Por qué?**: Separar datos de acceso (CustomUser) de datos operativos (Employee). Un empleado puede no tener cuenta de login.

---

#### 4. **FinancialOperation** (dashboard/models.py)
**Propósito**: Registrar cada ingreso/egreso del negocio.

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | PK | ID único |
| kind | CharField(choices) | INCOME (ingreso) / EXPENSE (egreso) |
| category | CharField(choices) | SERVICE / PRODUCT / OTHER |
| amount | DecimalField | Monto de la operación |
| occurred_on | DateField | Fecha del movimiento |
| description | CharField | Descripción/notas |
| created_by_id | FK→CustomUser | Quién registró la operación |
| employee_id | FK→Employee (nullable) | Empleado responsable de la operación |
| created_at | DateTime | Cuándo se registró |
| updated_at | DateTime | Última actualización |

**¿Por qué?**: Trazabilidad completa (quién, cuándo, qué, descripción).

---

#### 5. **ActivityLog** (dashboard/models.py)
**Propósito**: Auditoría - registrar todas las acciones en el sistema.

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | PK | ID único |
| action | CharField(choices) | CREATE / UPDATE / TOGGLE |
| entity_type | CharField | Tipo del objeto (Employee, Operation, etc.) |
| entity_id | IntegerField | ID de la entidad modificada |
| title | CharField | Resumen de la acción |
| details | TextField | Información adicional |
| performed_by_id | FK→CustomUser | Quién hizo la acción |
| created_at | DateTime | Cuándo ocurrió |

**¿Por qué?**: Cumplimiento legal y auditoría (quién hizo qué y cuándo).

---

### Relaciones y Constrains

```
CustomUser (1) ──── (0..1) StripeCustomer
   │
   ├── (1) ──── (N) Employee
   │
   ├── (1) ──── (N) FinancialOperation (created_by)
   │
   └── (1) ──── (N) ActivityLog (performed_by)

Employee (1) ──── (N) FinancialOperation (employee)
```

**Integridad**:
- Si se elimina un User, se elimina su StripeCustomer (CASCADE)
- Si se elimina un User, sus FinancialOperation se quedan sin employee (SET_NULL)
- Si se elimina un Employee, sus operaciones quedan sin responsable (SET_NULL)

---

## Componentes Principales

### 1. Aplicación `accounts` (Gestión de Usuarios)

**Archivo**: `apps/accounts/models.py`

```python
class CustomUserManager(BaseUserManager):
    """
    Manager personalizado que crear usuarios con email en lugar de username.
    
    ¿Por qué?
    - Django por defecto usa username (complicado para SaaS)
    - Email es más seguro, único, y mejor UX
    - Facilita autenticación passwordless después
    """
    
    def create_user(self, email, password=None, **extra_fields):
        # Valida que email no esté vacío
        # Normaliza email (lowercase, etc)
        # Hashea contraseña
        # Guarda en BD

    def create_superuser(self, email, password=None, **extra_fields):
        # Crea admin con role ADMIN
        # es_staff=True, es_superuser=True
```

**Archivo**: `apps/accounts/forms.py`

```python
class CustomSignupForm(SignupForm):
    """
    Valida registro del usuario.
    
    - Email válido (regex RFC5322)
    - Sin puntos consecutivos (..)
    - Dominio válido
    """

class CustomLoginForm(LoginForm):
    """
    Valida login.
    
    - Convierte email a lowercase
    - Limpia espacios en blanco
    """
```

**¿Por qué estos archivos?**
- **models.py**: Define estructura de datos (quién es usuario)
- **forms.py**: Valida datos del usuario (qué es válido)
- **admin.py**: Panel administrador (gestión en backend)

---

### 2. Aplicación `dashboard` (Panel Principal)

**Archivo**: `apps/dashboard/models.py`

**Modelo Employee**:
```python
class Employee(models.Model):
    """
    Perfil operativo de empleado.
    
    ¿Por qué separado de CustomUser?
    - Un empleado puede NO tener acceso al sistema (sin login)
    - Un usuario puede NO ser empleado registrado
    - Separación de concerns: acceso vs. operacional
    
    Roles:
    - MANAGER: puede ver todos los reportes
    - EMPLOYEE: solo ve sus operaciones
    """
    user = models.OneToOneField(CustomUser, ...)  # Opcional
    full_name = models.CharField(max_length=150)
    role = models.CharField(choices=Role.choices)  # gerente/empleado
    phone = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)  # Activo/Inactivo
    hired_at = models.DateField()  # Desde cuándo trabaja
```

**Modelo FinancialOperation**:
```python
class FinancialOperation(models.Model):
    """
    Registra ingresos/egresos.
    
    Campos clave:
    - kind: INCOME (ingreso) o EXPENSE (egreso)
    - category: SERVICE (servicio), PRODUCT (producto), OTHER (otro)
    - amount: Cantidad de dinero
    - occurred_on: Fecha del movimiento (importante para reportes)
    - created_by: Quién lo registró (trazabilidad)
    - employee: Quién fue responsable (opcional)
    
    ¿Por qué esta estructura?
    - Auditoría completa (trazabilidad)
    - Reportes por fecha, categoría, empleado
    - Búsqueda y filtrado flexible
    """
    kind = CharField(choices=Kind.choices)  # income/expense
    category = CharField(choices=Category.choices)  # service/product/other
    amount = DecimalField(max_digits=10, decimal_places=2)
    occurred_on = DateField()  # Fecha del evento
    description = CharField(max_length=255, blank=True)
    created_by = ForeignKey(CustomUser, on_delete=CASCADE)  # Auditoría
    employee = ForeignKey(Employee, null=True, blank=True)  # Responsable
```

**Modelo ActivityLog**:
```python
class ActivityLog(models.Model):
    """
    Auditoría del sistema.
    
    Registra TODAS las acciones:
    - Quién (performed_by)
    - Qué (action: create/update/toggle)
    - Dónde (entity_type, entity_id)
    - Cuándo (created_at)
    
    ¿Por qué?
    - Cumplimiento legal
    - Investigación de cambios
    - Historial de cambios
    """
    action = CharField(choices=Action.choices)  # create/update/toggle
    entity_type = CharField(max_length=50)  # Employee, Operation, etc
    entity_id = IntegerField()  # ID de qué se modificó
    title = CharField(max_length=255)  # Resumen
    details = TextField(blank=True)  # Detalles
    performed_by = ForeignKey(CustomUser, null=True)  # Quién
```

---

**Archivo**: `apps/dashboard/views.py`

**¿Qué son las vistas?**
Funciones Python que reciben una request HTTP y retornan una response (HTML, JSON, etc).

**Estructura típica**:
```python
@login_required  # Solo usuarios autenticados
@require_http_methods(['GET'])  # Solo GET, no POST
def dashboard_home(request):
    """
    Página principal del dashboard.
    
    Flujo:
    1. Obtener fecha actual y primer día del mes
    2. Consultar operaciones del usuario para hoy y este mes
    3. Calcular totales (ingresos/egresos)
    4. Renderizar template con datos
    """
    today = localdate()
    month_start = today.replace(day=1)
    
    # Óbtengo operaciones del USUARIO actualmente logueado
    day_operations = _scope_operations_for_user(
        request.user,
        FinancialOperation.objects.filter(occurred_on=today)
    )
    
    # Calculo sumas
    day_income = _sum_amount(day_operations.filter(kind=INCOME))
    day_expense = _sum_amount(day_operations.filter(kind=EXPENSE))
    
    # Paso datos al template
    context = {
        'day_income': day_income,
        'day_expense': day_expense,
        # ...
    }
    return render(request, 'dashboard/home.html', context)
```

**Funciones auxiliares**:

```python
def _can_manage_employees(user):
    """Retorna True si usuario puede gerenciar empleados."""
    return user.role in {'admin', 'gerente'}

def _scope_operations_for_user(user, queryset):
    """
    ¿Por qué existe?
    - Control de acceso a nivel de datos
    - Si es admin/gerente: ve TODAS las operaciones
    - Si es empleado: ve solo sus operaciones
    
    Seguridad: evita que empleado vea datos de otros
    """
    if user.role in {'admin', 'gerente'}:
        return queryset  # Ve todo
    return queryset.filter(created_by=user)  # Ve solo lo suyo

def _apply_operation_filters(request, queryset):
    """
    Aplica filtros desde URL a queryset:
    - kind: income/expense
    - category: service/product/other
    - employee: ID del empleado
    - q: búsqueda en descripción
    - min_amount/max_amount: rango de monto
    - sort: ordernar por
    
    ¿Por qué?
    - Buscar es esencial para usuarios
    - Filtrar por fechas, categoría, etc
    - UX: fácil encontrar transacciones
    """
    # Valida cada filtro
    # Aplica al queryset
    # Retorna queryset filtrado + dict de filtros seleccionados

def _log_activity(*, action, entity_type, entity_id, title, details='', performed_by=None):
    """
    Registra en ActivityLog.
    
    Se llama CADA VEZ que se:
    - Crea un empleado
    - Modifica una operación
    - Activa/desactiva algo
    
    Importancia: auditoría legal, investigación, historial
    """
    ActivityLog.objects.create(...)
```

---

**Archivo**: `apps/dashboard/urls.py`

```python
urlpatterns = [
    path('', dashboard_home, name='home'),
    path('profile/', user_profile, name='profile'),
    path('employees/', employees_list, name='employees'),
    path('employees/create/', create_employee, name='create_employee'),
    # ... etc
]
```

**¿Por qué existe?**
- Mapear URLs a vistas
- Nombre de URL para templates (`{% url 'dashboard:employees' %}`)
- Organización: cada app maneja sus URLs

---

**Archivo**: `apps/dashboard/tasks.py`

```python
from django.core.mail import send_mail

@task  # Django 6.0 task decorator
def send_email_async(email, subject, message):
    """
    Tarea asincrónica (background).
    
    ¿Por qué?
    - Enviar email es lento (1-5 seg)
    - Sería horrible si usuario espera
    
    Con @task:
    - Se encola en background
    - Usuario ve respuesta inmediata
    - Se envía email luego
    
    Se llama así:
    send_email_async.enqueue(
        email='user@example.com',
        subject='...',
        message='...'
    )
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
```

---

### 3. Aplicación `landing` (Páginas Públicas)

**Archivo**: `apps/landing/views.py`

```python
@require_http_methods(['GET'])
def home(request):
    """
    Página de inicio pública.
    
    Se ve si NO estás logueado.
    Si ESTÁS logueado → redirige a /dashboard/
    
    Datos:
    - Lista de features
    - Call-to-action (signup)
    """
    features = [
        {'title': 'Control Diario', 'description': '...'},
        # ...
    ]
    context = {'features': features}
    return render(request, 'landing/home.html', context)
```

**¿Por qué existe?**
- Mostrar qué es el producto
- Atraer nuevos usuarios
- Páginas como: Home, Features, Pricing

---

### 4. Aplicación `subscriptions` (Stripe)

**Archivo**: `apps/subscriptions/models.py`

```python
class StripeCustomer(models.Model):
    """
    Vinculación entre usuario y Stripe.
    
    Campos:
    - user: referencia a CustomUser
    - stripe_customer_id: ID en Stripe
    - stripe_subscription_id: ID de suscripción activa
    - subscription_status: active, canceled, past_due
    
    ¿Por qué?
    - Stripe es externo → guardar referencias locales
    - Sincronizar webhooks de Stripe
    - Saber si usuario pagó o no
    
    Ejemplo:
    Cliente paga → Stripe envía webhook
    → Guardamos subscription_id
    → Otorgamos acceso a features premium
    """
    user = OneToOneField(CustomUser, on_delete=CASCADE)
    stripe_customer_id = CharField(max_length=255)
    stripe_subscription_id = CharField(max_length=255, blank=True)
    subscription_status = CharField(max_length=50, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

---

## Explicación de Archivos Clave

### Archivo: `core/settings.py`

**¿Qué es?**
Configuración central de Django. Define cómo funciona TODA la aplicación.

**Secciones importantes**:

```python
# 1. Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',           # Panel admin
    'django.contrib.auth',            # Sistema auth
    'django.contrib.contenttypes',    # Tipos de contenido
    'django.contrib.sessions',        # Sesiones de usuario
    'django.contrib.messages',        # Mensajes (notifications)
    'django.contrib.staticfiles',     # CSS, JS, imágenes
    'django.contrib.sites',           # Multi-sitio
    
    # Apps de terceros
    'allauth',                        # Autenticación
    'tailwind',                       # Tailwind CSS
    'django_htmx',                    # HTMX
    
    # Nuestras apps
    'apps.accounts',
    'apps.dashboard',
    'apps.landing',
    'apps.subscriptions',
]

# 2. Middleware (procesa cada request)
MIDDLEWARE = [
    'SecurityMiddleware',             # Headers de seguridad
    'WhiteNoiseMiddleware',           # Servir static files
    'SessionMiddleware',              # Sesiones
    'CsrfViewMiddleware',             # CSRF protection
    'AuthenticationMiddleware',       # Autenticación
    'ContentSecurityPolicyMiddleware', # CSP headers
    'django_htmx.middleware.HtmxMiddleware',  # HTMX
]

# 3. Modelo de usuario personalizado
AUTH_USER_MODEL = 'accounts.CustomUser'

# 4. Base de datos
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3'
    )
}
# En producción, DATABASE_URL = 'postgres://...'

# 5. Email (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

**¿Por qué existe?**
- Django necesita saber qué apps, qué BD, qué seguridad
- Centralizar configuración evita bugs
- Mismo settings para desarrollo y producción

---

### Archivo: `core/urls.py`

**¿Qué es?**
Mapa principal de URLs de la aplicación.

```python
urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),     # SEO
    path('admin/', admin.site.urls),                       # /admin/
    path('accounts/', include('allauth.urls')),            # /accounts/login, /accounts/signup
    path('', include('apps.landing.urls')),                # / (home, features, pricing)
    path('dashboard/', include('apps.dashboard.urls')),    # /dashboard/ (panel principal)
]
```

**¿Por qué?**
- Django es modular (cada app tiene sus URLs)
- Este archivo las agrupa
- URLs claras, organizadas, mantenibles

---

### Archivo: `manage.py`

**¿Qué es?**
Ejecutable que ejecuta comandos Django.

```bash
python manage.py runserver      # Inicia servidor desarrollo
python manage.py migrate        # Aplica migraciones BD
python manage.py makemigrations # Crea migraciones
python manage.py createsuperuser # Crea admin
python manage.py shell          # Consola interactiva
python manage.py seed_data      # Datos de prueba
```

**¿Por qué existe?**
- CLI de Django
- Simplifica tareas administrativas
- Standalone (no necesita otra herramienta)

---

### Archivo: `requirements.txt`

**¿Qué es?**
Lista de dependencias Python.

```
Django==6.0.0
django-allauth==0.54.0
stripe==5.4.0
gunicorn==20.1.0
dj-database-url==1.2.0
django-htmx==1.16.0
whitenoise==6.4.0
ruff==0.0.250
```

**¿Por qué existe?**
- Reproducibilidad (cualquiera puede instalar mismo entorno)
- Compatible con `pip install -r requirements.txt`
- Versionado (qué versión exacta de cada paquete)

---

### Archivo: `Makefile`

**¿Qué es?**
Automatización de comandos comunes.

```makefile
make install    # python -m venv venv + pip install -r requirements.txt
make run        # python manage.py runserver
make migrate    # makemigrations + migrate
make test       # python manage.py test
make seed       # seed_data
make lint       # ruff check
make format     # ruff format
make superuser  # createsuperuser
```

**¿Por qué existe?**
- DX (Developer Experience): no recordar comandos largos
- Instalación rápida para nuevos devs
- Documentación en código

---

## Roles y Permisos

### Estructura de Roles

```
┌─────────────────────────────────────────────────────────────┐
│                    ADMINISTRADOR                            │
├─────────────────────────────────────────────────────────────┤
│ ✓ Ver todos los reportes                                    │
│ ✓ Crear/editar/eliminar empleados                          │
│ ✓ Ver auditoría (ActivityLog)                              │
│ ✓ Crear operaciones (manuales)                             │
│ ✓ Acceso a panel admin                                     │
│ ✓ Gestionar suscripción                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      GERENTE                                │
├─────────────────────────────────────────────────────────────┤
│ ✓ Ver todos los reportes                                    │
│ ✓ Crear operaciones                                        │
│ ✓ Crear/editar/eliminar empleados                          │
│ ✗ No acceso a panel admin                                  │
│ ✗ No auditoría                                             │
│ ✗ No cambiar suscripción                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      EMPLEADO                               │
├─────────────────────────────────────────────────────────────┤
│ ✓ Crear operaciones (solo propias)                          │
│ ✓ Ver sus operaciones                                       │
│ ✗ Ver operaciones de otros                                  │
│ ✗ Crear empleados                                          │
│ ✗ Ver reportes globales                                    │
│ ✗ Ver auditoría                                            │
└─────────────────────────────────────────────────────────────┘
```

### Implementación en Código

```python
# En CustomUser
class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    MANAGER = 'gerente', 'Gerente'
    EMPLOYEE = 'empleado', 'Empleado'

role = models.CharField(max_length=20, choices=Role.choices)

@property
def is_manager(self):
    """True si es admin o gerente."""
    return self.role in {self.Role.ADMIN, self.Role.MANAGER}


# En vistas
def _can_manage_employees(user):
    return user.is_authenticated and user.role in {'admin', 'gerente'}

@login_required
@require_http_methods(['GET'])
def employees_list(request):
    if not _can_manage_employees(request.user):
        return HttpResponseForbidden("No tienes permiso")
    
    employees = Employee.objects.all()
    return render(request, 'dashboard/employees.html', {'employees': employees})


# En scoping de datos
def _scope_operations_for_user(user, queryset):
    """Retorna solo lo que usuario puede ver."""
    if user.role in {'admin', 'gerente'}:
        return queryset  # Ve todo
    return queryset.filter(created_by=user)  # Ve solo lo suyo
```

---

## Flujo de Datos

### Flujo 1: Autenticación (Signup/Login)

```
Usuario → URL /accounts/signup
    ↓
Django carga template signup.html
    ↓
Usuario ingresa email + contraseña
    ↓
CustomSignupForm.clean() valida
    - Email válido (regex)
    - Email único
    - Contraseña segura
    ↓
Si válido:
    CustomUserManager.create_user()
        - Normaliza email
        - Hashea contraseña (bcrypt)
        - Guarda en BD
    ↓
    Envía email de verificación (tarea background)
    ↓
Usuario hace click en link
    ↓
Email confirmado → cuenta activa
    ↓
Redirige a /dashboard/

Si inválido:
    Muestra errores en formulario
    Usuario intenta de nuevo
```

---

### Flujo 2: Registrar Operación Financiera

```
Usuario logueado → URL /dashboard/operations/new
    ↓
Vista: create_operation (POST)
    ↓
Formulario con:
    - kind: income/expense (select)
    - category: service/product/other
    - amount: $$$
    - occurred_on: fecha
    - description: notas
    - employee: quién es responsable
    ↓
Validación:
    - amount > 0
    - amount es número válido
    - employee existe y is_active
    ↓
Si válido:
    FinancialOperation.objects.create(
        kind=kind,
        category=category,
        amount=amount,
        occurred_on=occurred_on,
        description=description,
        created_by=request.user,  # Auditoría
        employee=employee,
    )
    ↓
    Automáticamente log actividad:
    _log_activity(
        action='create',
        entity_type='FinancialOperation',
        entity_id=operation.id,
        title=f'Ingreso/Egreso de ${amount}',
        details=description,
        performed_by=request.user
    )
    ↓
    messages.success("Operación registrada")
    ↓
    Redirige a /dashboard/operations/ (lista)

Si inválido:
    messages.error("Error en formulario")
    Rerendering con errores
```

---

### Flujo 3: Ver Reportes

```
Gerente → URL /dashboard/reports?start=2024-01-01&end=2024-01-31
    ↓
Vista: reports_view (GET)
    ↓
Parsea parámetros URL:
    start_date = 2024-01-01
    end_date = 2024-01-31
    ↓
Construye queryset base:
    queryset = FinancialOperation.objects
        .filter(occurred_on__range=(start_date, end_date))
        .select_related('employee', 'created_by')
    ↓
Aplica filtros ADICIONALES (búsqueda):
    - kind: filtra income/expense
    - category: filtra service/product
    - employee: filtra por empleado
    - q: busca en description
    - min_amount/max_amount: rango
    ↓
Agrupa y suma:
    day_income = queryset.filter(kind='income').aggregate(Sum('amount'))
    day_expense = queryset.filter(kind='expense').aggregate(Sum('amount'))
    by_employee = queryset.values('employee').annotate(total=Sum('amount'))
    ↓
Genera PDF/CSV (si usuario pidió):
    workbook = openpyxl.Workbook()
    sheet.append([date, kind, amount, description, ...])
    ... (llenar toda la hoja)
    return HttpResponse(
        file_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=reporte.xlsx'}
    )
    ↓
    Navegador descarga archivo
    ↓
    Usuario abre en Excel

Si visualización HTML:
    context = {
        'operations': queryset[:50],  # 50 por página
        'total_income': day_income,
        'total_expense': day_expense,
        'net_result': day_income - day_expense,
        'filters': {...}  # Para mostrar filtros aplicados
    }
    return render(request, 'dashboard/reports.html', context)
```

---

### Flujo 4: Stripe Webhook (Suscripción Pagada)

```
Usuario llena formulario de pago en Stripe → Payment Success
    ↓
Stripe genera evento: customer.subscription.updated
    ↓
Stripe envía HTTP POST a: /subscriptions/webhook/
    ↓
Vista: stripe_webhook (POST)
    ↓
Verifica firma webhook (seguridad):
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = stripe.Webhook.construct_event(
        payload,
        sig_header,
        STRIPE_WEBHOOK_SECRET
    )
    ↓
    Si firma inválida → 400 Unauthorized
    ↓
Procesa evento:
    if event['type'] == 'customer.subscription.updated':
        stripe_customer_id = event['data']['object']['customer']
        subscription_id = event['data']['object']['id']
        status = event['data']['object']['status']
        
        # Busca StripeCustomer
        stripe_customer = StripeCustomer.objects.get(
            stripe_customer_id=stripe_customer_id
        )
        
        # Actualiza
        stripe_customer.stripe_subscription_id = subscription_id
        stripe_customer.subscription_status = status
        stripe_customer.save()
        
        # Log
        _log_activity(
            action='update',
            entity_type='StripeCustomer',
            entity_id=stripe_customer.id,
            title=f'Suscripción actualizada: {status}',
            performed_by=stripe_customer.user
        )
    ↓
    return HttpResponse(status=200)  # Ack Stripe
    ↓
Usuario ve en dashboard:
    "Tu suscripción está activa ✓"
```

---

## Características Principales

### 1. **Control Diario de Operaciones**

**¿Qué permite?**
- Registrar ingreso/egreso en segundos
- Ver totales del día/mes en tiempo real
- Filtrar por categoría, empleado, fecha
- Búsqueda full-text

**¿Cómo funciona?**
- Formulario simple (5 campos)
- Validación en cliente (Alpine.js) + servidor (Django)
- Guardado inmediato a BD
- Actualización de dashboard en vivo (HTMX)

**¿Por qué es importante?**
- Dueño necesita saber ganancias diarias
- Auditoría: quién registró, cuándo, qué
- Decisiones rápidas basadas en datos

---

### 2. **Gestión de Empleados**

**¿Qué permite?**
- Crear, editar, desactivar empleados
- Asignar rol (gerente, empleado)
- Vincular con usuarios del sistema
- Historial de contratación

**¿Cómo funciona?**
- Admin/Gerente accede a /dashboard/employees/
- Formulario: nombre, rol, teléfono, fecha contratación
- Backend valida datos
- Se crea registro Employee
- Se registra en ActivityLog (auditoría)

**¿Por qué es importante?**
- Saber quién trabaja, en qué rol
- Historial de personal (auditoría)
- Control de permisos (quién ve qué)

---

### 3. **Reportes y Análisis**

**¿Qué permite?**
- Ver ganancias/pérdidas por período
- Filtrar por categoría, empleado, tipo
- Descargar como Excel/PDF
- Gráficos y estadísticas

**¿Cómo funciona?**
- User elige rango de fechas
- Backend agrega datos (SUM, COUNT, GROUP BY)
- Genera tabla o archivo
- Usuario descarga

**¿Por qué es importante?**
- Dueño toma decisiones basadas en datos
- Identifica tendencias (qué vende bien)
- Evalúa desempeño de empleados

---

### 4. **Autenticación Email-Only**

**¿Qué permite?**
- Signup con solo email + contraseña
- Sin username (más simple)
- Link de verificación por email
- Password reset por email

**¿Cómo funciona?**
- Usuario ingresa email
- CustomUserManager crea usuario
- Envía link de verificación (tarea bg)
- Usuario verifica
- Su cuenta se activa

**¿Por qué es importante?**
- UX simplificada (menos campos)
- Email es identificador único
- Seguro (no namespaces colisionables)

---

### 5. **Suscripción con Stripe**

**¿Qué permite?**
- Planes pagos (free, pro, enterprise)
- Pago recurrente (mensual, anual)
- Manejo autorizado de pagos
- Webhooks para sincronización

**¿Cómo funciona?**
- Usuario selecciona plan
- Redirige a Stripe
- Ingresa tarjeta
- Stripe cobra
- Webhook actualiza BD
- Acceso a features premium

**¿Por qué es importante?**
- Modelo SaaS (ingresos)
- Seguridad (Stripe maneja datos sensibles)
- Escalable (puede crecer sin límites)

---

### 6. **Auditoría y ActivityLog**

**¿Qué permite?**
- Ver historial de TODAS las acciones
- Quién modificó qué, cuándo, por qué
- Trazabilidad total del sistema
- Cumplimiento legal

**¿Cómo funciona?**
- Cada acción (create, update, delete) llama `_log_activity()`
- Se guarda: quién, qué, cuándo, detalles
- No se puede modificar (solo lectura)
- Admin ve en /dashboard/audit/

**¿Por qué es importante?**
- Legal (regulaciones, requerimientos)
- Seguridad (detectar cambios sospechosos)
- Accountability (quién es responsable de qué)

---

### 7. **Interfaz Simple y Responsiva**

**¿Qué permite?**
- Usar en desktop, tablet, móvil
- Interfaz intuitiva (sin jerga técnica)
- Carga rápida
- Sin JavaScript complejo

**¿Cómo funciona?**
- Tailwind CSS (utility-first)
- Alpine.js (interactividad sin reload)
- HTMX (cambios sin page refresh)
- Mobile-first design

**¿Por qué es importante?**
- Usuarios pueden trabajar desde cualquier lado
- Experiencia consistente
- Performance (carga rápido)

---

## Stack Técnico Detallado

### Backend

```
           Django 6.0 (Framework Web)
                    |
    ┌───────────────┼───────────────┐
    │               │               │
 Models.py       Views.py      URLs.py
  (BD)         (Lógica)        (Rutas)
    │               │               │
    └───────────────┼───────────────┘
                    |
           django-allauth
          (Autenticación)
                    |
    ┌───────────────┼───────────────┐
    │               │               │
  Stripe API    Email SMTP      Celery Tasks
 (Pagos)      (Notificaciones)  (Background)
```

### Frontend

```
                  Django Templates
                      |
        ┌─────────────┼─────────────┐
        |             |             |
    Tailwind CSS   Alpine.js      HTMX
    (Estilos)    (Interactividad) (AJAX)
        |             |             |
        └─────────────┼─────────────┘
                      |
                Navegador Usuario
```

### Base de Datos

```
                  SQL (Queries)
                      |
        ┌─────────────┼─────────────┐
        |             |             |
    Django ORM    Migraciones    Queries
  (Abstracción)   (Versionado)   (SQL)
        |             |             |
        └─────────────┼─────────────┘
                      |
        ┌─────────────┴─────────────┐
        |                           |
    SQLite              PostgreSQL
  (Desarrollo)        (Producción)
```

---

## Seguridad Implementada

### 1. **CSRF Protection (Cross-Site Request Forgery)**
```python
# En templates
<form method="POST">
    {% csrf_token %}  # Token único por sesión
    ...
</form>
```
**¿Por qué?**: Evita que sitios maliciosos hagan requests a nombre del usuario.

### 2. **HTTPS/Seguridad de Headers**
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = 'DENY'
```

### 3. **Content Security Policy (CSP)**
```python
SECURE_CSP = CSP(
    script_src=("'self'",),
    style_src=("'self'",),
)
```
**¿Por qué?**: Previene vulnerabilidades XSS (inyección de código).

### 4. **SQL Injection Prevention**
```python
# ❌ VULNERABLE
query = f"SELECT * FROM users WHERE email = {user_email}"

# ✓ SEGURO (Django ORM)
user = User.objects.filter(email=user_email)
```
**¿Por qué?**: Django ORM parameteriza queries automáticamente.

### 5. **Authentication & Authorization**
```python
@login_required  # Solo usuarios autenticados
def dashboard_home(request):
    if not request.user.is_authenticated:
        redirect('/accounts/login/')
    ...
```

### 6. **Password Hashing**
```python
# Django hashea automáticamente con bcrypt
user.set_password('contraseña123')
user.save()
# Nunca se guarda texto plano
```

### 7. **Stripe Webhook Verification**
```python
sig_header = request.META['HTTP_STRIPE_SIGNATURE']
event = stripe.Webhook.construct_event(
    payload,
    sig_header,
    STRIPE_WEBHOOK_SECRET
)
```
**¿Por qué?**: Verifica que webhook realmente vino de Stripe, no un atacante.

---

## Deploy (Producción)

### Variables de Entorno (`.env`)
```
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu@gmail.com
EMAIL_HOST_PASSWORD=app-password
```

### Servidor
```
Gunicorn (app server)
  ├─ 4 workers
  └─ listening en 0.0.0.0:8000

Nginx (reverse proxy)
  ├─ HTTPS (Let's Encrypt)
  ├─ Cache headers
  └─ Load balancer

PostgreSQL (BD)
  └─ Backups diarios

Redis (Cache/Celery)
  └─ Sessions
```

### Checklist Deploy
- [ ] DEBUG = False
- [ ] SECRET_KEY = valor secreto
- [ ] ALLOWED_HOSTS = dominios reales
- [ ] DATABASE_URL = PostgreSQL
- [ ] HTTPS habilitado
- [ ] Logs configurados
- [ ] Backups BD
- [ ] Email SMTP ok
- [ ] Stripe keys (live)
- [ ] Monitoreo (Sentry, etc)

---

## Conclusión

Este sistema es una **plataforma SaaS moderna** que demuestra:

1. **Arquitectura limpia**: Modular, escalable, mantenible
2. **Seguridad**: CSRF, CSP, SQL injection prevention, auth
3. **Buenas prácticas**: Auditoría, validación, separación de concerns
4. **Escalabilidad**: Stripe, background tasks, BD flexible
5. **UX**: Interfaz simple, intuitiva, responsive

**Stack**: Django + PostgreSQL + Stripe + Tailwind + Alpine = **Producción-ready**

