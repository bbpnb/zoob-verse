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
        group = click.Group(
            self.name,
            help=self.description,
        )

        @group.command("ingest")
        @click.option("--xlsx", "xlsx_path", type=click.Path(exists=True), help="Feishu xlsx file")
        @click.option("--files", "file_paths", type=click.Path(exists=True), multiple=True, help="Text files")
        def ingest(xlsx_path, file_paths):
            """Import data into the module."""
            click.echo(f"[{self.name}] Ingesting data...")
            if xlsx_path:
                click.echo(f"  xlsx: {xlsx_path}")
            if file_paths:
                for fp in file_paths:
                    click.echo(f"  file: {fp}")
            click.echo(f"[{self.name}] Done.")

        @group.command("index")
        @click.option("--novel", type=click.Path(exists=True), help="Novel text file to index")
        def index(novel):
            """Build knowledge graph index."""
            click.echo(f"[{self.name}] Building index...")
            if novel:
                click.echo(f"  novel: {novel}")
            click.echo(f"[{self.name}] Done.")

        @group.command("query")
        @click.argument("question")
        @click.option("--type", "query_type", type=click.Choice(["fact", "reasoning"]), default="fact",
                      help="Query type: fact (RAG) or reasoning (graph)")
        def query(question, query_type):
            """Query the knowledge graph."""
            click.echo(f"[{self.name}] Query ({query_type}): {question}")

        @group.command("analyze")
        @click.option("--type", "method", type=click.Choice([
            "shortest-path", "community-detection", "centrality", "custom"
        ]), required=True)
        @click.option("--from", "from_entity", help="Source entity (for shortest-path)")
        @click.option("--to", "to_entity", help="Target entity (for shortest-path)")
        def analyze(method, from_entity, to_entity):
            """Run analysis on the knowledge graph."""
            click.echo(f"[{self.name}] Analyzing ({method})...")
            if method == "shortest-path":
                click.echo(f"  from: {from_entity} → to: {to_entity}")

        return group
