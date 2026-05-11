# ADR-001: Arquitectura Modular Basada en Django Apps

**Estado:** ✅ Aceptado  
**Fecha:** 2026-05-10  
**Contexto:** Fase 0 — Definición  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

Necesitamos construir un ERP que sea:
1. **Modular** — Se pueda instalar/desinstalar módulos
2. **Extensible** — Terceros puedan crear módulos
3. **Multi-tenant** — Una instancia, múltiples empresas
4. **Evolucionable** — Actualizar módulos sin romper core

Opción 1: **Microservicios** (cada módulo es servicio independiente)  
Opción 2: **Monolito modular** (Django apps, pero cargadas dinámicamente)

---

## 🎯 Decisión

**Elegimos Opción 2: Monolito modular con Django apps**

- Cada módulo es una Django app (`facturacion_ec`, `inventory`)
- Apps registradas dinámicamente vía `ModuleRegistry`
- Módulos viven en repositorios separados
- Core no conoce módulos específicos (solo contrato)

---

## 📐 Arquitectura

```
erp-nexus/                    # Core repo
├── apps/                     # 11 Django apps (core)
├── modules/                  # ⚠️ Dev only: módulos locales
│   └── facturacion_ec/       # En prod, se instalan en ~/.erp-nexus/modules/
└── erp_nexus/modules_enabled.py  # AUTO-GENERADO
```

**ModuleRegistry** (`apps/core_marketplace/models.py`):

```python
class Module(models.Model):
    technical_name = models.CharField(unique=True)
    version = models.CharField()
    enabled = models.BooleanField(default=False)
    installed_at = models.DateTimeField()
    module_path = models.CharField()  # Ruta física (git clone)
```

**apps.py de cada módulo:**

```python
class FacturacionEcConfig(AppConfig):
    name = "modules.facturacion_ec"
    verbose_name = "Facturación Ecuador"
```

**apps.py del core:**

```python
# erp_nexus/apps.py
def ready(self):
    from apps.core_marketplace.registry import ModuleRegistry
    ModuleRegistry.load_enabled()
```

---

## ✅ Ventajas

| Ventaja | Explicación |
|---------|-------------|
| **Simplicidad** | Un solo Django project, un solo servidor |
| **Performance** | Sin network calls entre servicios |
| **Transactions** | ACID en toda la operación (factura → inventory) |
| **Shared cache** | Redis común para todos los módulos |
| **Developer friendly** | Devs conocen Django, no necesitan aprender microservicios |
| **Deploy simple** | Un solo `docker-compose up` |
| **Testing** | Tests end-to-end sin mocks de red |

---

## ⚠️ Desventajas y Mitigaciones

| Desventaja | Mitigación |
|------------|------------|
| **Coupling潜在地** | Enforce ModuleSpec + code reviews |
| **Un solo proceso** | Celery para tareas pesadas (async) |
| **Scalability limits** | Sharding por company para 1000+ empresas |
| **Downtime en deploy** | Blue-green deployment con Docker |

---

## 🔍 Alternativas Consideradas

### **Opción A: Microservicios full**

| Aspecto | Decisión |
|---------|----------|
| Cada módulo = servicio gRPC/REST | ❌ Rechazado |
| Service mesh (Istio) | ❌ Overkill |
| Docker por módulo | ❌ Complejidad innecesaria |
| Message bus (Kafka/RabbitMQ) | ✅ **Usamos Event Bus interno** (Django signals) |

**Razón rechazo:** Demasiada complejidad para < 100 empresas. Monolito es suficiente.

### **Opción B: Django plugins tradicionales**

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "facturacion_ec",      # Instalado vía pip
    "inventory",           # Instalado vía pip
]
```

**Problema:** Dependencias pip → lockfile gigante, conflictos de versiones, imposible actualizar módulos independientemente.

**Solución nuestra:** Módulos como **directorios sueltos** (no paquetes pip), registro dinámico.

### **Opción C: Django + django-modular**

Existía `django-modular` pero:
- Inactivo (último commit 2018)
- No soporta multi-company
- Sin marketplace engine

---

## 📋 Reglas de Modularidad

1. **ModuleSpec (contrato):** Todo módulo debe tener `__meta__.py` con Metadata válida
2. **AppConfig único:** Cada módulo → `apps.py` con `AppConfig`
3. **Models company-bound:** TODOS los modelos deben tener `ForeignKey(Company)`
4. **No imports hardcodeados:** Usar `apps.get_model()` para referenciar otros módulos
5. **Events no coupling:** Comunicación solo vía Event Bus, no imports directos

```python
# ❌ MAL — acoplamiento fuerte
from inventory.models import Product

# ✅ BIEN — Event Bus
EventBus.emit("invoice.created", payload={...})
# inventory se suscribe y actualiza stock
```

---

## 🧪 Validación

El `ModuleInstaller` verifica:

```python
def validate_module(path: Path):
    # 1. __meta__.py existe
    assert (path / "__meta__.py").exists()

    # 2. Meta válida (import sin errores)
    meta = import_module_meta(path)

    # 3. apps.py existe + subclass de AppConfig
    assert issubclass(app_config, AppConfig)

    # 4. models.py importable
    import_module(f"{technical_name}.models")

    # 5. All models tienen 'company' field
    for model in apps.get_models():
        assert hasattr(model, "company")

    # 6. No dependencies circulares (check graph)
    assert not has_circular_deps(meta["dependencies"])
```

---

## 📈 Impacto en Equipo

| Rol | Impacto |
|-----|---------|
| **Dev módulos** | Escriben módulos independientes (sin tocar core) |
| **Dev core** | Mantienen ModuleRegistry + marketplace engine |
| **DevOps** | Deploy único (todos los módulos) |
| **Clients** | Instalan solo módulos que necesitan |

---

## 🔄 Implicaciones en el Roadmap

**Semana 2-4:** Módulo `facturacion_ec` como referencia  
**Semana 5-6:** Extraer `facturacion_ec` a repo separado  
**Semana 7+:** Nuevos módulos (`inventory`, `sales`) en sus propios repos

---

## 📚 Referencias

- **Django Apps:** https://docs.djangoproject.com/en/dev/ref/applications/
- **Microservices vs Monolith:** [Martin Fowler](https://martinfowler.com/bliki/MonolithFirst.html)
- **Plugin Architectures:** [Plugin Pattern](https://en.wikipedia.org/wiki/Plugin architecture)

---

**Consecuencia:** Hemos elegido el camino del **monolito bien modularizado**. Más simple, más rápido de desarrollar, suficiente para la escala esperada.

**Siguiente ADR:** ADR-002 (Event Bus como medio de comunicación)
