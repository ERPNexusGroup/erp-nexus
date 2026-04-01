# Contributing to ERP Nexus

## Git Flow

We use [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/):

```
main        ← Producción (stable releases)
  └── dev   ← Integración (trabajo activo)
        ├── feature/core-events
        ├── feature/django-ninja-api
        ├── feature/install-module-cmd
        └── fix/migration-order
```

### Rules

1. **Nunca commit directo a `main`** — solo merges desde `dev` con PR aprobado
2. **Trabaja en `dev` o en branches `feature/*`** desde `dev`
3. **PRs a `dev`** requieren review antes de merge
4. **Releases**: `dev` → PR → `main` con tag semver (v0.2.0)

### Branch naming

- `feature/description` — nueva funcionalidad
- `fix/description` — corrección de bug
- `refactor/description` — refactorización
- `docs/description` — documentación

### Commits

Usa [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add install_module management command
fix: handle missing __meta__.py in sync_modules
refactor: split settings into base/dev/production
docs: update README with new architecture
test: add tests for core_events EventBus
chore: add django-ninja dependency
```

## Development setup

```bash
# Clone
git clone https://github.com/ERPNexusGroup/erp-nexus.git
cd erp-nexus
git checkout dev

# Install dependencies
uv sync

# Setup DB
uv run python manage.py migrate
uv run python manage.py bootstrap_superadmin --username admin --email admin@local --password changeme

# Run dev server
uv run python manage.py runserver

# Run tests
uv run pytest
```

## Project conventions

- Apps del core van en `apps/core_*`
- Módulos externos van en `modules/`
- Management commands: `apps/<app>/management/commands/`
- Settings: `erp_nexus/settings/base.py` (shared), `development.py`, `production.py`
- Migrations: auto-generated, review before commit

## Pull Request checklist

- [ ] Tests pasan (`uv run pytest`)
- [ ] Migrations revisadas
- [ ] CHANGELOG.md actualizado
- [ ] Convención de commits seguida
- [ ] Documentación actualizada si aplica
