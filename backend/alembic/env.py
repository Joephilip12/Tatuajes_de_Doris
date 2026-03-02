from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

# Alembic Config object, provides access to values within the .ini file in use.
config = context.config

# Configure Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- IMPORTANT: import your SQLAlchemy Base + models so Alembic can autogenerate ----
from app.db import Base, engine  # noqa: E402
from app import models  # noqa: F401, E402  (ensures model metadata is registered)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Offline mode uses a URL and does not create an Engine.
    We still read the URL from env via app.db if possible, but Alembic's offline
    mode expects a URL string. We'll prefer sqlalchemy.url from alembic.ini if set;
    otherwise fall back to engine.url.
    """
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        # Fallback to the application's engine URL (from DATABASE_URL env var)
        url = str(engine.url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    We reuse the application's engine, which is configured from DATABASE_URL.
    """
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()