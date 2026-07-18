"""
Job Hunter AI - Modelo de Dados do Currículo
Mapeia a tabela 'resume' e define seus atributos e relacionamentos.
"""

from typing import Any, Dict, Optional
import uuid
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class Resume(Base):
    """
    Representa o currículo de um usuário no ecossistema Job Hunter AI.
    Contém o texto extraído, metadados do documento e a carga estruturada por IA.
    """

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Chave estrangeira vinculando o currículo ao seu respectivo usuário."
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Nome original do arquivo enviado pelo usuário (ex: curriculo_2026.pdf)."
    )

    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="Caminho do armazenamento local ou URL da nuvem para recuperação do arquivo físico."
    )

    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Texto bruto extraído diretamente do PDF pelos mecanismos de parsing."
    )

    # Armazenamento JSON estruturado de alto desempenho no PostgreSQL (JSONB)
    structured_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Objeto JSON estruturado pela IA contendo chaves como competências, experiências e educação."
    )

    # Relacionamentos Bidirecionais
    user: Mapped["User"] = relationship("User", backref="resumes")