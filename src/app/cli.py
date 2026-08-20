import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from src.config import get_config
from src.app.bootstrap import ensure_superuser
from src.app.domain_service import DomainService

@click.command("create-superuser")
@with_appcontext
def create_superuser_command() -> None:
    """Bootstrap the superuser account from SUPERUSER_* env vars."""
    config = current_app.extensions["config"]
    domain_service: DomainService = current_app.extensions["domain_service"]
    ensure_superuser(domain_service, config)
    click.echo("Superuser ensured.")

def register_cli(app: Flask) -> None:
    app.cli.add_command(create_superuser_command)
