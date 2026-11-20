"""Flask CLI commands."""

from __future__ import annotations

import click


def register_cli(app) -> None:
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Drop and recreate all tables before seeding.")
    def seed_command(reset: bool) -> None:
        """Create the deterministic demo dataset."""
        from app.seed import seed_database

        seed_database(reset=reset)
        click.echo("Seed complete.")

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create tables without running migrations (local fallback)."""
        from app import models  # noqa: F401
        from app.core.db import db

        db.create_all()
        click.echo("Tables created.")
