"""
ERP Nexus Django settings — compatibility shim.

The real settings live in `erp_nexus.settings` package (base.py, development.py, etc).
This file re-exports for backwards compatibility.
"""
import os
from erp_nexus.settings import *  # re-export from modular settings
