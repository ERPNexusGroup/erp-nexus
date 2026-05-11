# 📦 Instalación — ERP Nexus

**Tiempo estimado:** 10-15 minutos  
**Requisitos:** Python 3.11+, uv, PostgreSQL (opcional para prod)

---

## 📋 Tabla Rápida

| Entorno | Comando | Tiempo |
|----------|---------|--------|
| **Desarrollo** | `make dev` | 10 min |
| **Producción** | `make prod` | 20 min |
| **Docker Compose** | `docker-compose up` | 5 min |

---

## 🐍 Opción 1: Instalación Manual (Desarrollo)

### **1. Prerrequisitos**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
                    postgresql postgresql-contrib \
                    redis-server \
                    libpq-dev gcc build-essential \
                    curl wget git

# macOS (con Homebrew)
brew install python postgresql redis

# Windows (WSL2 recomendado)
wsl --install Ubuntu
# Luego seguir guía Linux dentro de WSL
```

### **2. Clonar repositorio**

```bash
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus

# Crear branch de trabajo (desde dev)
git checkout dev
```

### **3. Instalar dependencias con uv**

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias del proyecto
uv sync

# Activar entorno virtual
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows
```

### **4. Configurar base de datos**

```bash
# Opción A: SQLite (desarrollo rápido)
# Ya configurado por defecto en settings/development.py

# Opción B: PostgreSQL (recomendado para testing)
sudo -u postgres createuser -s $USER
createdb erp_nexus_dev

# Editar .env
cp .env.example .env
# DATABASE_URL=postgres://user:pass@localhost/erp_nexus_dev
```

### **5. Aplicar migraciones**

```bash
uv run python manage.py migrate

# Crear superusuario
uv run python manage.py createsuperuser
# Username: admin
# Email: admin@local
# Password: ********
```

### **6. Cargar datos iniciales**

```bash
# Catálogos SRI (Ecuador), estados, etc.
uv run python manage.py bootstrap_data

# Opcional: datos de ejemplo
uv run python manage.py loaddata fixtures/initial_data.json
```

### **7. Iniciar servidor**

```bash
# Desarrollo (auto-reload)
uv run python manage.py runserver

# Producción (Gunicorn)
uv run gunicorn erp_nexus.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**Accede:** http://localhost:8000/admin

---

## 🐳 Opción 2: Docker Compose (Recomendado)

### **Ventajas:**
- Todo en un comando
- PostgreSQL + Redis incluidos
- Igual a producción

### **1. Clonar + levantar:**

```bash
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus

# CopiarVariables de entorno
cp .env.example .env
# Editar .env si es necesario (por defecto funciona)

# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web
```

### **2. Migraciones + superuser:**

```bash
# Ejecutar comandos Django en contenedor
docker-compose exec web uv run python manage.py migrate
docker-compose exec web uv run python manage.py bootstrap_superadmin \
  --username admin \
  --email admin@local \
  --password admin123

# Acceso a shell
docker-compose exec web uv run python manage.py shell
```

### **3. Servicios disponibles:**

| Servicio | Puerto | URL |
|----------|--------|-----|
| ERP Nexus | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| PGAdmin (opcional) | 5050 | http://localhost:5050 |

**Detener:**
```bash
docker-compose down          # Mantiene volúmenes (datos)
docker-compose down -v       # Elimina volúmenes (limpia todo)
```

---

## ☁️ Opción 3: Nexus CLI (Futuro)

```bash
# Instalar CLI
pip install nexus-cli

# Inicializar proyecto
nexus init mi-erp --with-docker

# Iniciar
nexus server start
```

---

## 🛠️ Post-Instalación

### **Configurar módulos:**

```bash
# Listar módulos disponibles
uv run python manage.py module list

# Instalar módulo desde git
uv run python manage.py install_module \
  --git https://github.com/ERPNexus/facturacion_ec.git

# O desde directorio local
uv run python manage.py install_module ./modules/facturacion_ec

# Activar módulo
uv run python manage.py module enable facturacion_ec

# Aplicar migraciones del módulo
uv run python manage.py migrate
```

### **Configurar settings:**

```python
# erp_nexus/settings/development.py
INSTALLED_APPS += [
    "modules.facturacion_ec",
]

# Variables de entorno
FACTURACION_EC_AMBIENTE = 1  # 1=Pruebas, 2=Prod
FACTURACION_EC_AUTO_SEND = False
```

### **Crear datos de prueba:**

```bash
# Catálogos SRI (EC)
uv run python manage.py loaddata facturacion_ec/fixtures/sri_catalogs.json

# Empresa de prueba
uv run python manage.py shell -c "
from core_companies.models import Company
Company.objects.create(
    name='Mi Empresa Demo',
    tax_id='1791234567001',
    ruc='1791234567001'
)
"
```

---

## 🔧 Configuración Avanzada

### **Variables de entorno (.env):**

```bash
# Core
DJANGO_SECRET_KEY=tu-secret-key-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@localhost/erp_nexus
# o SQLite
DATABASE_URL=sqlite:///./db.sqlite3

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu@email.com
EMAIL_HOST_PASSWORD=tu-contraseña

# Facturación Ecuador
FACTURACION_EC_AMBIENTE=1
FACTURACION_EC_AUTO_SEND=False
FACTURACION_EC_CERT_PATH=/path/to/cert.p12
FACTURACION_EC_CERT_PASSWORD=

# API externas
OPENROUTER_API_KEY=sk-or-...
```

### **settings/development.py vs production.py:**

```python
# development.py
DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
CELERY_TASK_ALWAYS_EAGER = True  # Tasks sync

# production.py
DEBUG = False
ALLOWED_HOSTS = ["erp.miempresa.com"]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CELERY_BROKER_URL = os.getenv("REDIS_URL")
```

---

## 🐛 Troubleshooting

### **Error: "no module named '...'"**

```bash
# Solución 1: activar venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# Solución 2: reinstalar
uv sync --reinstall
```

### **Error: "relation does not exist"**

```bash
# Aplicar migraciones
uv run python manage.py migrate

# Si falla, recrear DB
uv run python manage.py flush  # CUIDADO: borra datos!
uv run python manage.py migrate
```

### **Error: "port 8000 already in use"**

```bash
# Matar proceso
lsof -ti:8000 | xargs kill -9

# O usar otro puerto
uv run python manage.py runserver 0.0.0.0:8080
```

### **PostgreSQL: "role does not exist"**

```bash
# Crear usuario
sudo -u postgres createuser -s $USER
createdb erp_nexus_dev

# O en docker, el user ya está creado
docker-compose exec db psql -U erp_nexus -c "\du"
```

### **Módulo no aparece en marketplace:**

```bash
# Verificar __meta__.py
uv run python manage.py module validate facturacion_ec

# Sincronizar módulos
uv run python manage.py module sync

# Check
uv run python manage.py module list
```

---

## ✅ Verificación

```bash
# 1. Health check API
curl http://localhost:8000/api/health/

# Respuesta esperada:
# {"status": "ok", "version": "0.5.0", "database": "ok"}

# 2. Admin accesible
# Abre: http://localhost:8000/admin
# Login con superuser creado

# 3. Modules instalados
curl http://localhost:8000/api/modules/

# 4. Tests
uv run pytest -q

# Todos must PASS ✅
```

---

## 🚀 Primeros Pasos Post-Instalación

1. **Login en admin** → Crear Company
2. **Instalar módulo facturacion_ec** (si necesitas facturación)
3. **Configurar** → Variables de entorno
4. **Crear** → Cliente + Producto + Factura de prueba
5. **Verificar** → Factura aparece en dashboard

---

## 📦 Actualizar ERP Nexus

```bash
# Pull cambios
git checkout dev
git pull origin dev

# Actualizar dependencias
uv sync

# Migraciones
uv run python manage.py migrate

# Recolectar static (prod)
uv run python manage.py collectstatic --noinput

# Reiniciar server
# Ctrl+C y correr de nuevo
```

---

## 🧹 Limpiar Instalación

```bash
# Eliminar DB + datos
rm db.sqlite3  # SQLite
# o
dropdb erp_nexus_dev  # PostgreSQL

# Recrear desde cero
uv run python manage.py migrate
uv run python manage.py bootstrap_superadmin ...
```

---

## 📞 Soporte

- **Issues:** github.com/ERPNexus/erp-nexus/issues
- **Discussions:** github.com/ERPNexus/erp-nexus/discussions
- **Docs:** erpnexus.ec/docs (futuro)

---

**¿Instalación exitosa?** → Lee `DEVELOPMENT.md` para empezar a desarrollar.
