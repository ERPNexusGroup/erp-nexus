#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def main() -> None:
    # Añadir modules/ al path para imports dinámicos
    BASE_DIR = Path(__file__).resolve().parent
    modules_dir = BASE_DIR / "modules"
    if str(modules_dir) not in sys.path:
        sys.path.insert(0, str(modules_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp_nexus.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
