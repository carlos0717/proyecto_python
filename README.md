# Django SaaS Boilerplate

Kit de inicio para construir aplicaciones SaaS con Django. Incluye autenticación, pagos, panel de control y despliegue.

Este proyecto se encuentra alojado en el siguiente repositorio de GitHub:

**Repositorio:** [https://github.com/carlos0717/proyecto_python.git](https://github.com/carlos0717/proyecto_python.git)

<div align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-CDN-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"/>
</div>

---

## Instrucciones para configurar el proyecto

Sigue estos pasos para configurar y ejecutar el proyecto en tu computadora:

### 1. Clonar el repositorio

```bash
git clone https://github.com/carlos0717/proyecto_python.git
cd proyecto_python
```

### 2. Crear y activar un entorno virtual

En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

En macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo según sea necesario:
```bash
cp .env.example .env
```
Edita el archivo `.env` para configurar la base de datos, correo electrónico y otros ajustes.

### 5. Aplicar migraciones

Ejecuta los siguientes comandos para configurar la base de datos:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Poblar datos de demostración

Para crear usuarios, empleados y operaciones de prueba, ejecuta:
```bash
python manage.py seed_data
```

Credenciales de prueba:
- **Administrador:** `admin@example.com` / `admin123`
- **Gerente:** `gerente@peluqueria.local` / `gerente123`
- **Empleado:** `empleado@peluqueria.local` / `empleado123`

### 7. Ejecutar el servidor de desarrollo

Inicia el servidor con:
```bash
python manage.py runserver
```

Accede a la aplicación en **http://localhost:8000**.

---

## Cuándo y por qué revisar los archivos PRD_pelu.md y proyecto.md

- **PRD_pelu.md**: Este archivo contiene los requisitos del proyecto, incluyendo los objetivos principales, las funcionalidades esperadas y las necesidades del cliente. Es importante revisarlo al iniciar el desarrollo o al realizar cambios significativos para asegurarse de que el proyecto cumple con los requisitos establecidos.

- **proyecto.md**: Este archivo documenta detalles técnicos del proyecto, como la estructura, las decisiones de diseño y las convenciones utilizadas. Es útil revisarlo al integrar nuevas funcionalidades o al realizar revisiones de código para garantizar que se sigan las mejores prácticas y se mantenga la coherencia en el desarrollo.

---

## Características principales

- **Modelo de usuario personalizado** — inicio de sesión solo con correo electrónico.
- **Autenticación** — registro, inicio de sesión, verificación de correo, restablecimiento de contraseña.
- **Suscripciones con Stripe** — API de métodos de pago, webhooks, seguimiento de estado.
- **Panel de usuario** — navegación lateral, perfil, ajustes, preferencias de notificación.
- **Planes de suscripción** — planes administrados desde el panel de administrador.
- **Tareas en segundo plano** — Decorador `@task()` nativo de Django 6.0.
- **Política de seguridad de contenido (CSP)** — Middleware integrado en Django 6.0.
- **Archivos estáticos** — Servidos con WhiteNoise.
- **Despliegue** — Listo para Railway/Heroku/VPS con Gunicorn y Procfile.
- **Datos de prueba** — Comando único para poblar datos de demostración.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0, Python 3.12 |
| Auth | django-allauth (email-only) |
| Payments | Stripe (Payment Methods API) |
| Frontend | Tailwind CSS (CDN), Alpine.js, HTMX |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Static files | WhiteNoise |
| Server | Gunicorn |
| Tasks | Django 6.0 native `@task()` |
| Linting | Ruff |

## Quick start

```bash
git clone https://github.com/carlos0717/proyecto_python.git
cd proyecto_python
make install
cp .env.example .env
make migrate
python manage.py seed_data
make run
```

Visit **http://localhost:8000** — admin login: `admin@example.com` / `admin123`

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Create virtualenv and install dependencies |
| `make run` | Start development server |
| `make migrate` | Run makemigrations + migrate |
| `make test` | Run 16 tests |
| `make seed` | Populate demo data (admin + plans) |
| `make lint` | Lint with ruff |
| `make format` | Format with ruff |
| `make superuser` | Create admin user |
| `make clean` | Remove __pycache__ files |

## Project structure

```
django-saas-boilerplate/
├── core/
│   ├── settings.py           # All config via env vars
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/             # CustomUser (email-only), admin
│   │   ├── models.py         # CustomUser + CustomUserManager
│   │   ├── admin.py
│   │   └── tests.py          # 6 tests
│   ├── dashboard/            # Dashboard, profile, settings
│   │   ├── models.py         # SubscriptionPlan, UserSettings
│   │   ├── views.py          # dashboard, profile, settings, plans
│   │   ├── tasks.py          # Background email tasks
│   │   ├── tests.py          # 6 tests
│   │   └── management/commands/seed_data.py
│   ├── subscriptions/        # Stripe integration
│   │   ├── models.py         # StripeCustomer
│   │   └── views.py          # checkout, webhooks
│   └── landing/              # Public pages
│       ├── views.py          # home, features, pricing, robots.txt
│       └── tests.py          # 4 tests
├── templates/
│   ├── base.html             # Public layout (nav + footer)
│   ├── account/              # 20 allauth templates (styled)
│   ├── dashboard/            # Dashboard layout + pages
│   ├── landing/              # Home, features, pricing
│   └── subscriptions/        # Stripe checkout
├── static/css/               # Design system CSS
├── CLAUDE.md                 # AI editor context
├── Makefile                  # Dev commands
├── Procfile                  # Deployment
├── pyproject.toml            # Ruff config
├── requirements.txt
└── .env.example
```

## Environment variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
DEBUG=True
SECRET_KEY=your-secret-key

# Database (default: SQLite)
# DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Email (default: console backend)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```
