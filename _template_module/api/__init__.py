"""API del módulo mi_modulo."""
from ninja import Router

from .routes import router as example_router

# Export router para incluir en API principal
router = example_router
