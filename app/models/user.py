"""
Job Hunter AI - Modelo de Dados do Usuário
Mapeia a tabela 'user' e seus atributos no banco de dados.
"""

from typing import Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class User(Base):
    """
    Representa o usuário/candidato no ecossistema Job Hunter AI.
    Centraliza credenciais de acesso, status da conta e relacionamentos de domínio.
    """
    
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Nome completo do usuário."
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="E-mail único utilizado para login e notificações."
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Hash seguro da senha gerado via bcrypt."
    )
    
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Telefone/WhatsApp do usuário no formato internacional (ex: +5511999999999)."
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Sinaliza se o usuário está ativo no sistema ou se teve a conta desativada."
    )
    
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Sinaliza privilégios administrativos dentro da plataforma."
    )

    # Relacionamentos (Serão mapeados conforme os novos modelos forem criados)
    # Exemplo futuro:
    # resumes: Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")