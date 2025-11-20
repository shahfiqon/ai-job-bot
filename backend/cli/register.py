from __future__ import annotations

import getpass

import typer
from loguru import logger
from rich.console import Console
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth import get_password_hash
from app.db import SessionLocal
from app.models.user import User
from cli.main import app

console = Console()


@app.command("register-user")
def register_user(
    username: str = typer.Option(..., prompt=True, help="Username for the new user"),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Password for the new user",
    ),
) -> None:
    """Register a new user in the database."""
    db = SessionLocal()
    try:
        # Check if users table exists
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        if "users" not in inspector.get_table_names():
            console.print("[red]Error: Users table does not exist[/]")
            console.print("[yellow]Please run the database migration first:[/]")
            console.print("[yellow]  cd backend && alembic upgrade head[/]")
            raise typer.Exit(code=1)
        # Strip whitespace from password (but warn if it was there)
        original_password = password
        password = password.strip()
        if password != original_password:
            console.print("[yellow]Warning: Password had leading/trailing whitespace which was removed[/]")
        
        # Validate password length
        if len(password) < 8:
            console.print(f"[red]Error: Password must be at least 8 characters long (got {len(password)})[/]")
            raise typer.Exit(code=1)

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_password)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        console.print(f"[green]✓[/] User [bold]{username}[/] registered successfully!")
        console.print(f"User ID: {new_user.id}")
    except IntegrityError:
        db.rollback()
        console.print(f"[red]Error: Username [bold]{username}[/] already exists[/]")
        raise typer.Exit(code=1)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while registering user: {e}")
        console.print("[red]Error: Failed to register user due to database error[/]")
        raise typer.Exit(code=1)
    except ValueError as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"Validation error while registering user: {e}")
        console.print(f"[red]Error: {error_msg}[/]")
        raise typer.Exit(code=1)
    except Exception as e:
        db.rollback()
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Unexpected error while registering user: {error_msg}")
        
        if error_msg:
            console.print(f"[red]Error: An unexpected error occurred: {error_msg}[/]")
        else:
            console.print("[red]Error: An unexpected error occurred (no error message)[/]")
            console.print("[yellow]Please check the logs for more details[/]")
        raise typer.Exit(code=1)
    finally:
        db.close()

