"""Module base class — all research modules must inherit from this."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import click
import yaml


class ModuleBase(ABC):
    """Base class for all research modules.

    Each module (jinyong, gulong, liucixin, etc.) defines its own
    entity types, relationship types, extraction logic, and analysis.
    The core engine handles generic graph operations.
    """

    name: str = ""
    description: str = ""

    def __init__(self, module_dir: Path):
        self.module_dir = module_dir
        self.config_dir = module_dir / "config"
        self.data_dir = module_dir / "data"
        self._config: dict = {}

    def load_config(self) -> dict:
        """Load module config from config/settings.yaml."""
        config_path = self.config_dir / "settings.yaml"
        if config_path.exists():
            with open(config_path) as f:
                self._config = yaml.safe_load(f) or {}
        return self._config

    @abstractmethod
    def get_entity_types(self) -> list[str]:
        """Return list of entity types for this module."""
        ...

    @abstractmethod
    def get_relationship_types(self) -> list[str]:
        """Return list of relationship types for this module."""
        ...

    @abstractmethod
    def extract(self, text: str) -> tuple[list[dict], list[dict]]:
        """Extract entities and relationships from text.

        Returns:
            (entities, relationships) where each is a list of dicts.
        """
        ...

    @abstractmethod
    def analyze(self, graph: Any, method: str, **kwargs) -> Any:
        """Run module-specific analysis on the graph."""
        ...

    def get_cli(self) -> click.Group:
        """Return the CLI command group for this module."""
        return click.Group(
            self.name,
            help=self.description,
        )
