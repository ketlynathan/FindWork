"""
Job Hunter AI - Modelo de Dados de Candidaturas (Applications)
Mapeia a tabela 'job_application' e gerencia o pipeline de status e score.
"""

from typing import Optional
import uuid
from sqlalchemy import String, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class JobApplication(Base):
    """
    Representa o ciclo de vida de uma candidatura de um usuário a uma vaga específica.
    Centraliza o score de compatibilidade da IA e o status da automação de inscrição.
    """

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Vínculo com o usuário dono da candidatura."
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Vínculo com a vaga alvo."
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resume.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Vínculo com a versão do currículo que foi (ou será) usada nesta candidatura."
    )

    # Métricas de IA (Calculadas pelo RankingAgent)
    match_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Pontuação de 0.00 a 100.00 que define a aderência do candidato à vaga."
    )

    match_rationale: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Justificativa qualitativa gerada pela IA detalhando os prós e contras da vaga."
    )

    # Controle de Fluxo / Status da Automação
    # Estados esperados: 'PENDING_ANALYSIS', 'WAITING_APPROVAL', 'APPROVED', 'APPLYING', 'APPLIED', 'REJECTED_BY_USER', 'FAILED'
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING_ANALYSIS",
        nullable=False,
        index=True,
        doc="Status atual da vaga dentro do funil de automação do sistema."
    )

    error_logs: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Registros de falhas técnicas caso o ApplyAgent encontre problemas no formulário."
    )

    # Relacionamentos Bidirecionais Eager/Lazy configurados explicitamente
    user: Mapped["User"] = relationship("User", backref="applications")
    job: Mapped["Job"] = relationship("Job", backref="applications")
    resume: Mapped["Resume"] = relationship("Resume", backref="applications")