"""
conftest global — parchea modules_enabled antes de que Django se inicie.
"""
import sys
from types import ModuleType

# Intercepta la importación de erp_nexus.modules_enabled
mock_modules = ModuleType("modules_enabled")
mock_modules.MODULE_APPS = []
sys.modules.setdefault("erp_nexus.modules_enabled", mock_modules)
