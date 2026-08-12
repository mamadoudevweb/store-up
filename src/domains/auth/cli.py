"""Auth domain CLI commands."""
from __future__ import annotations

import click
from flask import current_app
from flask.cli import with_appcontext

from src.domains.accounts.exceptions import (
    CredentialAlreadyExists,
    UsernameConflict,
    EmailConflict,
)


@click.command("bootstrap-superuser")
@click.option("--first-name", prompt="First Name", default="Super")
@click.option("--last-name", prompt="Last Name", default="Admin")
@click.option("--username", prompt="Username", default="admin")
@click.option("--email", prompt="Email", default="admin@example.com")
@click.option(
    "--password",
    prompt="Password",
    hide_input=True,
    confirmation_prompt=True,
)
@with_appcontext
def bootstrap_superuser(first_name, last_name, username, email, password):
    """Creates a superuser account interactively."""
    account_service = current_app.extensions["account_service"]

    try:
        # 1. Create account
        account_res = account_service.account.create_account(
            first_name=first_name, last_name=last_name
        )
        account_id = account_res.data.id

        # 2. Set credentials
        account_service.credential.set_credentials(
            account_id=account_id,
            username=username,
            email=email,
            password=password,
        )
        
        click.secho(f"Superuser '{username}' created successfully!", fg="green")

    except UsernameConflict:
        click.secho(f"Error: Username '{username}' already exists.", fg="red")
    except EmailConflict:
        click.secho(f"Error: Email '{email}' already exists.", fg="red")
    except CredentialAlreadyExists:
        click.secho(f"Error: Account already has credentials.", fg="red")
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg="red")
