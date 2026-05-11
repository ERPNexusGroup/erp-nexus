"""
Marketplace Registry — Sistema de registro de repositorios de módulos.

Permite registrar fuentes de módulos (git repos, URLs) y buscar
módulos disponibles para instalar.
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone


class ModuleRegistry(models.Model):
    """
    Fuente de módulos (repositorio git, URL de catálogo).
    """
    SOURCE_TYPES = [
        ("github", "GitHub Repository"),
        ("git", "Git Repository"),
        ("url", "URL (JSON catalog)"),
        ("local", "Local Path"),
    ]

    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default="github")
    url = models.URLField(max_length=500, help_text="URL del repositorio o catálogo")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    priority = models.IntegerField(default=50, help_text="Prioridad de búsqueda (mayor = primero)")

    # Cache de módulos encontrados
    cached_modules = models.JSONField(default=dict, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "name"]
        verbose_name = "Module Registry"
        verbose_name_plural = "Module Registries"

    def __str__(self):
        return f"{self.name} ({self.source_type})"

    def sync(self) -> int:
        """
        Sincroniza la lista de módulos disponibles desde la fuente.
        Retorna el número de módulos encontrados.
        """
        if self.source_type in ("github", "git"):
            return self._sync_from_git()
        elif self.source_type == "url":
            return self._sync_from_url()
        return 0

    def _sync_from_git(self) -> int:
        """Lee __meta__.py de repositorios en la organización."""
        # Para GitHub, buscar repos en la organización
        # Ejemplo: https://github.com/ERPNexusGroup
        import subprocess
        try:
            # Listar repos de la org
            result = subprocess.run(
                ["gh", "repo", "list", self._extract_org(), "--limit", "50",
                 "--json", "name,description,url"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return 0

            repos = json.loads(result.stdout)
            modules = {}
            for repo in repos:
                name = repo["name"]
                # Filtrar por prefijo o patrón de módulo
                if self._is_module_repo(name):
                    modules[name] = {
                        "name": name,
                        "description": repo.get("description", ""),
                        "source": repo.get("url", ""),
                        "type": "module",
                    }

            self.cached_modules = modules
            self.last_sync = timezone.now()
            self.save(update_fields=["cached_modules", "last_sync"])

            # Limpiar cache
            cache.delete(f"registry:{self.name}")

            return len(modules)
        except Exception:
            return 0

    def _sync_from_url(self) -> int:
        """Descarga catálogo JSON desde URL."""
        import urllib.request
        try:
            with urllib.request.urlopen(self.url, timeout=10) as response:
                data = json.loads(response.read().decode())

            modules = {}
            items = data if isinstance(data, list) else data.get("items", data.get("modules", []))
            for item in items:
                name = item.get("technical_name", item.get("name", ""))
                if name:
                    modules[name] = item

            self.cached_modules = modules
            self.last_sync = timezone.now()
            self.save(update_fields=["cached_modules", "last_sync"])

            return len(modules)
        except Exception:
            return 0

    def _extract_org(self) -> str:
        """Extrae la organización de la URL."""
        url = self.url.rstrip("/")
        parts = url.split("/")
        if "github.com" in url:
            return parts[-1] if len(parts) > 3 else "ERPNexusGroup"
        return "ERPNexusGroup"

    def _is_module_repo(self, name: str) -> bool:
        """Determina si un repositorio es un módulo ERP Nexus."""
        # Por ahora, cualquier repo que no sea los core repos
        core_repos = {"sdk-nexus", "nexus", "erp-nexus"}
        return name not in core_repos


class ModuleDownload(models.Model):
    """
    Registro de descargas de módulos.
    """
    module_name = models.CharField(max_length=100, db_index=True)
    version = models.CharField(max_length=50)
    source = models.CharField(max_length=500)
    downloaded_by = models.CharField(max_length=150, blank=True, default="")
    downloaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("success", "Success"),
            ("failed", "Failed"),
            ("pending", "Pending"),
        ],
        default="pending",
    )
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-downloaded_at"]
        verbose_name = "Module Download"
        verbose_name_plural = "Module Downloads"

    def __str__(self):
        return f"{self.module_name} v{self.version} — {self.status}"


def search_modules(
    query: str = "",
    registry_name: str = None,
    category: str = None,
) -> List[Dict[str, Any]]:
    """
    Busca módulos disponibles en los registros configurados.

    Args:
        query: Término de búsqueda
        registry_name: Nombre del registro (None = todos)
        category: Filtrar por categoría/dominio
    """
    results = []

    registries = ModuleRegistry.objects.filter(is_active=True)
    if registry_name:
        registries = registries.filter(name=registry_name)

    for registry in registries:
        # Usar cache si existe
        cache_key = f"registry:{registry.name}"
        modules = cache.get(cache_key)
        if modules is None:
            modules = registry.cached_modules or {}
            cache.set(cache_key, modules, 300)  # 5 min

        for name, info in modules.items():
            # Filtrar por query
            if query and query.lower() not in name.lower():
                desc = info.get("description", "")
                if query.lower() not in desc.lower():
                    continue

            # Filtrar por categoría
            if category and info.get("domain", "") != category:
                continue

            results.append({
                "name": name,
                "description": info.get("description", ""),
                "source": info.get("source", ""),
                "version": info.get("version", "latest"),
                "registry": registry.name,
            })

    return results
