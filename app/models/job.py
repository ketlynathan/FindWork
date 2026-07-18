"""
Job Hunter AI - Modelo de Dados da Vaga de Emprego
Mapeia a tabela 'job' e define seus atributos e índices de pesquisa.
"""

from typing import Any, Dict, Optional
from sqlalchemy import String, Text, Numeric, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class Job(Base):
    """
    Representa uma oportunidade de emprego capturada na internet.
    Contém dados brutos e estruturados necessários para ranqueamento e automação de inscrição.
    """

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Título oficial da vaga (ex: Desenvolvedor Python Sênior)."
    )

    company: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Nome da empresa contratante."
    )

    location: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        doc="Localidade da vaga (ex: São Paulo - SP, Remoto, Híbrido)."
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Descrição textual completa e bruta extraída do portal de origem."
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        nullable=False,
        doc="Link direto e exclusivo da vaga na plataforma de origem."
    )

    portal_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Identificador do portal coletor (ex: Gupy, LinkedIn, Indeed)."
    )

    salary_min: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Valor salarial mínimo estipulado ou extraído."
    )

    salary_max: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Valor salarial máximo estipulado ou extraído."
    )

    # Dados adicionais processados por IA (Ex: Tech Stack limpa, Senioridade inferida, Benefícios)
    structured_requirements: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Metadados estruturados extraídos da descrição (skills necessárias, certificações, benefícios)."
    )


# Criação de um Índice Composto para otimizar buscas combinadas efetuadas pelos agentes
Index("ix_job_portal_title", Job.portal_source, Job.title)