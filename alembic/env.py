import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. Importa as configurações do ecossistema e a Base Declarativa
from app.utils.config import get_settings
from app.database.base_class import Base

# 2. IMPORTANTE: Importar TODOS os modelos explicitamente para que o Alembic 
# consiga inspecioná-los e gerar as migrações automáticas via `--autogenerate`.
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.models.application import JobApplication

settings = get_settings()

# This is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define o target_metadata apontando para a nossa Base unificada
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation we don't even need a DB API to be available.
    """
    url = settings.sync_database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Executa as migrações dentro do contexto de uma conexão ativa."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    Como o Alembic roda de forma síncrona por padrão, interceptamos e criamos um fluxo assíncrono.
    """
    # Sobrescreve a URL do arquivo INI pela URL de conexão síncrona do Pydantic Settings
    # O Alembic utiliza o driver síncrono padrão para aplicar as migrações estruturais
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.sync_database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Como não estamos usando frameworks assíncronos complexos no escopo do CLI do Alembic,
    # executamos o fluxo estável online diretamente de forma limpa.
    asyncio.run(run_migrations_online())