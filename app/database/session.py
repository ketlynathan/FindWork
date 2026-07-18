"""
Job Hunter AI - Gerenciamento de Sessões do Banco de Dados
Configura e expõe os engines e factories do SQLAlchemy (Síncrono e Assíncrono).
"""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 1. Configuração do Motor Assíncrono (Utilizado em produção e nos Repositórios)
async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,  # Definir como True via logger se precisar inspecionar SQL cru
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
)

# 2. Configuração do Motor Síncrono (Utilizado pelo Alembic e CLI tools)
sync_engine = create_engine(
    settings.sync_database_url,
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
)

# 3. Factories de Sessões
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Alias para compatibilidade com a UI e serviços
db_session = AsyncSessionLocal

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Injection Generator para fornecer sessões assíncronas isoladas.
    Garante o fechamento automático da conexão e rollback em caso de falha.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database transaction failed. Rolling back.", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Generator[Session, None, None]:
    """
    Dependency Injection Generator para sessões síncronas.
    Utilizado principalmente em escopos de scripts isolados ou agendadores.
    """
    with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database sync transaction failed. Rolling back.", error=str(e))
            session.rollback()
            raise
        finally:
            session.close()


def init_db():
    """
    Cria todas as tabelas no banco de dados com base nos modelos mapeados,
    utilizando o engine síncrono.
    """
    from app.models.base import Base  # Importa o Base aqui para evitar importação circular
    
    logger.info("Mapeando tabelas e iniciando estrutura do banco de dados...")
    try:
        # Usa o sync_engine que você já configurou para criar a estrutura física
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Todas as tabelas foram criadas/validadas com sucesso.")
    except Exception as e:
        logger.error("Erro fatal ao inicializar tabelas estruturais do banco", error=str(e))
        raise e