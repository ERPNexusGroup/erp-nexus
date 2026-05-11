# 🤝 Guía de Contribución — ERP Nexus

**Gracias por considerar contribuir a ERP Nexus!**

Esta guía explica el workflow, estándares y proceso de revisión de PRs.

---

## 📋 Índice

1. [Cómo Contribuir](#cómo-contribuir)
2. [Proceso de PR](#proceso-de-pr)
3. [Estándares de Código](#estándares-de-código)
4. [Conventional Commits](#conventional-commits)
5. [Testing](#testing)
6. [Documentación](#documentación)
7. [Git Flow](#git-flow)
8. [Code Review](#code-review)

---

## 🚀 Cómo Contribuir

### **Reportar un Bug**
1. Buscar en [Issues existentes](https://github.com/ERPNexus/erp-nexus/issues)
2. Si no existe, crear issue con:
   - Título claro: `[BUG] Descripción breve`
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Entorno (OS, Python, Django version)
   - Logs/stack trace si aplica

### **Sugerir una Feature**
1. Buscar si ya existe propuesta
2. Crear issue con:
   - Título: `[FEATURE] Descripción`
   - Problema que resuelve
   - Solución propuesta (diseño/UX)
   - Alternativas consideradas

### **Enviar un PR**
1. **Fork** el repo
2. **Crear branch** desde `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feat/mi-feature
   ```
3. **Desarrollar** siguiendo [`.architecture/CODING_STANDARDS.md`](.architecture/CODING_STANDARDS.md)
4. **Tests** — Añadir/actualizar tests
5. **Docs** — Actualizar [`README.md`](../README.md) si es público
6. **Commit** — Seguir Conventional Commits
7. **Push** y abrir PR a `dev`

---

## 🔄 Proceso de PR

### **Checklist PR (obligatorio)**

**Antes de enviar:**
- [ ] Mi branch está actualizada con `dev` (rebased, no merge commit)
- [ ] Tests pasan localmente: `pytest -q`
- [ ] Linter OK: `ruff check .`
- [ ] Type hints: `mypy .` (0 errores)
- [ ] Cobertura no baja (si cambias tests)
- [ ] No hay secrets/credentials en el código
- [ ] `__meta__.py` actualizado (si es módulo)
- [ ] README actualizado (si es público)

**Al abrir PR:**
- [ ] Título siguiendo Conventional Commits
- [ ] Descripción clara: qué + por qué + cómo
- [ ] Referencia a issue (si aplica): `Closes #123`
- [ ] Screenshots (si es UI)
- [ ] Breaking changes documentados

**CI automático:**
- ✅ Tests (pytest)
- ✅ Lint (ruff)
- ✅ Type check (mypy)
- ✅ Security (bandit)

---

## 📝 Estándares de Código

**Todo el código debe seguir:** [`.architecture/CODING_STANDARDS.md`](.architecture/CODING_STANDARDS.md)

Resumen rápido:

| Aspecto | Regla |
|---------|-------|
| Indentación | 4 espacios (no tabs) |
| Línea máxima | 100 caracteres |
| Import order | stdlib → Django → third-party → local |
| Nombres | `snake_case` vars, `PascalCase` clases |
| Type hints | Obligatorios en funciones públicas |
| Docstrings | Google Style para funciones/clases públicas |
| Tests | pytest, `tests/` mirror de módulo |

---

## 📝 Conventional Commits

Formato: `<tipo>(<ámbito>): <descripción>`

### **Tipos:**
- `feat` — Nueva funcionalidad
- `fix` — Corrección de bug
- `docs` — Cambios documentación
- `style` — Formato (sin cambio funcional)
- `refactor` — Refactorización
- `perf` — Mejora performance
- `test` — Añadir/修正 tests
- `chore` — Mantenimiento (deps, CI, etc.)
- `build` — Cambios build system
- `ci` — Cambios CI/CD
- `revert` — Revertir commit

### **Ámbito (scope):**
- `core` — Cambios en core (apps/, settings)
- `marketplace` — Marketplace engine
- `facturacion_ec` — Módulo facturación
- `inventory` — Módulo inventario
- `api` — API endpoints
- `docs` — Documentación
- `ci` — Integración continua
- `deps` — Dependencias

### **Ejemplos:**
```bash
feat(facturacion_ec): add XML digital signature support
fix(api): correct company filter in invoice list
docs(architecture): update module installation diagram
test(core): add unit tests for ActiveCompanyMiddleware
chore(deps): update django-ninja to 3.1
refactor(models): split Invoice into header/detail tables
```

---

## 🧪 Testing

### **Requisitos:**
- Tests en `tests/` mirror de código fuente
- Cobertura >80% para módulos nuevos
- Tests unitarios + integración

### **Ejecutar tests:**
```bash
# Todos los tests
uv run pytest

# Módulo específico
uv run pytest apps/facturacion/tests/

# Con cobertura
uv run pytest --cov=modules.facturacion_ec --cov-report=html

# Un solo test
uv run pytest tests/test_models.py::TestInvoice::test_calculate_totals -v
```

### **Escribir tests:**
```python
# tests/test_models.py
import pytest
from modules.facturacion_ec.models import Invoice


@pytest.mark.django_db
class TestInvoice:
    def test_calculate_totals(self, invoice_factory, line_factory):
        """Totals calculation from lines."""
        invoice = invoice_factory()
        line_factory(invoice=invoice, quantity=2, unit_price=100)
        line_factory(invoice=invoice, quantity=1, unit_price=50)

        invoice.calculate_totals()
        assert invoice.subtotal == 250
        assert invoice.tax_total == 30  # 12% IVA
        assert invoice.total == 280
```

---

## 📚 Documentación

### **Qué documentar:**
- **Código público:** Docstrings (Google Style)
- **Módulos:** README.md con instalación, config, ejemplos
- **API endpoints:** Documentation strings en routes.py (Django Ninja auto-doc)
- **Configuración:** Comentarios en `__meta__.py`
- **Decisiones:** `ADR/` (Architecture Decision Records)

### **Docstring ejemplo:**
```python
def generate_access_key(
    ruc: str,
    ambiente: int,
    establishment_code: str,
    emission_point: str,
    sequential: str,
    date: Optional[datetime] = None
) -> str:
    """Genera la clave de acceso única del SRI (49 dígitos).

    Formato SRI: AAAAMMDD + 2d estab + 3d ptoEmi + 15d secuencial + 9d random

    Args:
        ruc: RUC empresa (13 dígitos)
        ambiente: 1=Pruebas, 2=Producción
        establishment_code: Código establecimiento (2 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        sequential: Número secuencial (9 dígitos)
        date: Fecha emisión (default: hoy)

    Returns:
        Clave acceso SRI (49 dígitos)

    Example:
        >>> generate_access_key("1791234567001", 1, "001", "001", "000000001")
        "2026051000010000000000000123456789"
    """
```

---

## 🌿 Git Flow

```
main            → Producción (solo release tags)
dev             ← Rama de desarrollo (PRs aquí)
feature/*       ←Features (feat/, fix/, docs/)
hotfix/*        ← Bugs urgentes (directo a main)
release/vX.Y.Z  ← Preparar release (merge a main + tag)
```

### **Workflow:**
```bash
# 1. Partir de dev actualizada
git checkout dev
git pull origin dev

# 2. Crear feature branch
git checkout -b feat/facturacion-email

# 3. Trabajar y commitear
git add .
git commit -m "feat(facturacion_ec): add email notification on approval"

# 4. Rebase contra dev antes de PR
git fetch origin
git rebase origin/dev

# 5. Push y PR
git push -u origin feat/facturacion-email
# Abrir PR en GitHub: dev ← feat/facturacion-email
```

**NO usar merge commits** en dev — usar rebase + fast-forward.

---

## 🔍 Code Review

### **Para reviewers:**
1. **Funcionalidad:** ¿Hace lo que dice? ¿Cubre el caso?
2. **Seguridad:** ¿Filtra por company? ¿Valida inputs?
3. **Performance:** ¿N+1 queries? ¿Índices necesarios?
4. **Tests:** ¿Hay tests? ¿Cubren edge cases?
5. **Docs:** ¿Docstrings? ¿README actualizado?
6. **Estilo:** ¿Sigue [`.architecture/CODING_STANDARDS.md`](.architecture/CODING_STANDARDS.md)?

### **Para autores:**
- Responder comentarios constructivamente
- Si no estás de acuerdo, discutir (no ignorar)
- Actualizar branch con feedback antes de merge

---

## 🏷️ labeling Issues/PRs

### **Labels:**
- `bug` — Bug report
- `enhancement` — Feature request
- `documentation` — Docs improvements
- `core` — Cambios en core ERP Nexus
- `module:facturacion_ec` — Módulo facturación Ecuador
- `module:inventory` — Módulo inventario
- `module:sales` — Módulo ventas
- `good first issue` — Para nuevos contribuyentes
- `priority:high` — Bloqueante
- `status:blocked` — Esperando algo

---

## 🎯 Kanban / Tablero

Usamos GitHub Projects:

| Column | Contenido |
|--------|-----------|
| Backlog | Issues nuevas sin priorizar |
| To Do | Priorizadas, listas para desarrollo |
| In Progress | Dev en curso |
| Review | PR abierto, esperando review |
| Done | Merged en dev |
| Won't Do | Rechazadas/duplicadas |

---

## 🆘 ¿Dónde pedir ayuda?

1. **GitHub Discussions** — Preguntas generales, ideas
2. **GitHub Issues** — Bugs específicos
3. **Pull Request comments** — Para código en revisión
4. **Email:** dev@erpnexus.ec (solo作为 último recurso)

---

## 🙏 Agradecimientos

ERP Nexus es posible gracias a la comunidad de contribuyentes. Cada PR, issue o documentación ayuda.

**¡Gracias por contribuir! 🚀**

---

**Última actualización:** 2026-05-10
