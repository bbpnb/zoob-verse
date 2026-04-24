"""graph-lore CLI — Literary Knowledge Graph Platform"""

import click
import importlib
import pkgutil
from pathlib import Path

from src.modules import base as module_base


def _discover_modules():
    """Dynamically discover all module packages under src.modules."""
    modules_path = Path(module_base.__file__).parent
    for finder, name, is_pkg in pkgutil.iter_modules([str(modules_path)]):
        if is_pkg and not name.startswith("_"):
            yield name


@click.group()
@click.version_option("0.1.0")
def main():
    """graph-lore — Literary Knowledge Graph Platform

    Build knowledge graphs from literary works for relationship mining,
    pattern discovery, and content generation.
    """
    pass


# Dynamically add module commands
for _mod_name in _discover_modules():
    try:
        mod = importlib.import_module(f"src.modules.{_mod_name}")
        if hasattr(mod, "cli"):
            main.add_command(mod.cli, name=_mod_name)
    except Exception:
        pass


if __name__ == "__main__":
    main()
