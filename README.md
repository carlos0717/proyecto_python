# Django SaaS Boilerplate

Kit de inicio para construir aplicaciones SaaS con Django. Incluye autenticación, pagos, panel de control y despliegue.

<div align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-CDN-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"/>
  <img src="https://img.shields.io/badge/Stripe-Payments-6772E5?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="Licencia: MIT"/>
</div>

---

## Instrucciones para configurar el proyecto

Sigue estos pasos para configurar y ejecutar el proyecto en tu computadora:

### 1. Clonar el repositorio

```bash
git clone https://github.com/eriktaveras/django-saas-boilerplate.git
cd django-saas-boilerplate
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
git clone https://github.com/eriktaveras/django-saas-boilerplate.git
cd django-saas-boilerplate
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

## Django 6.0 features used

This boilerplate uses three major features introduced in Django 6.0:

**Background Tasks** — Send emails asynchronously without Celery:
```python
from django.tasks import task

@task
def send_welcome_email(user_email):
    send_mail("Welcome!", "...", None, [user_email])

# In your view:
send_welcome_email.enqueue(user_email=user.email)
```

**Content Security Policy** — Built-in CSP middleware with nonce support:
```python
SECURE_CSP = {
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
}
```
```html
<script nonce="{{ csp_nonce }}" src="..."></script>
```

**Template Partials** — Reusable template components without separate files:
```html
{% partialdef stat_card inline %}
<div class="card">{{ card_title }}: {{ card_value }}</div>
{% endpartialdef %}

{% with card_title="Users" card_value="42" %}
    {% partial stat_card %}
{% endwith %}
```

## Deployment

### Railway

Push to GitHub and connect to Railway. The `Procfile` and `DATABASE_URL` handling are already configured.

### Heroku

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py seed_data
```

### VPS

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
gunicorn core.wsgi --bind 0.0.0.0:8000
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](LICENSE) for details.

---
