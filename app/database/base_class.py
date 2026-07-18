"""
Job Hunter AI - Base Declarativa do ORM
Define a classe base de onde todos os modelos de dados do banco herdarão.
"""

from datetime import datetime
import uuid
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """
    Classe base abstrata do SQLAlchemy 2.x para todos os modelos.
    Injeta ID auto-gerado como UUID, timestamps de auditoria e nome automático de tabela.
    """
    
    # 1. Geração automática do nome da tabela em snake_case com base no nome da classe
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Converte CamelCase para snake_case simplificado
        name = cls.__name__
        return "".join([f"_{c.lower()}" if c.isupper() and i > 0 else c.lower() for i, c in enumerate(name)])

    # 2. Chave Primária Universal (UUIDv4) indexada e não nula
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
        doc="Identificador único universal da entidade."
    )

    # 3. Timestamps de Auditoria Automatizados
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Data e hora de criação do registro no banco."
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Data e hora da última modificação do registro."
    )