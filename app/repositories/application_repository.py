"""
Job Hunter AI - Repositório de Candidaturas (Applications)
Implementação do padrão Repository para controle de estados do funil de automação.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application import JobApplication
from app.repositories.base_repository import BaseRepository


class JobApplicationRepository(BaseRepository[JobApplication]):
    """
    Repositório especializado para monitoramento e mutação do status de candidaturas.
    Alimenta diretamente a lógica de orquestração do funil executado pelos Agentes.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o repositório vinculando explicitamente o modelo JobApplication."""
        super().__init__(model=JobApplication, db_session=db_session)

    async def get_by_user_id(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[JobApplication]:
        """
        Recupera todo o histórico de interações e candidaturas de um usuário específico.
        
        Args:
            user_id: ID único (UUID) do candidato.
            skip: Quantidade de registros a saltar.
            limit: Limite máximo de registros para paginação.
            
        Returns:
            Lista de candidaturas ordenadas pela pontuação de compatibilidade (Score).
        """
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.match_score.desc().nulls_last(), self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, status: str, limit: int = 20) -> List[JobApplication]:
        """
        Busca em lote registros que correspondam a um status específico.
        Utilizado exaustivamente pelos Agentes (ex: carregar registros em 'APPROVED' para aplicar).
        
        Args:
            status: A string de estado do fluxo (ex: 'PENDING_ANALYSIS', 'APPROVED').
            limit: Quantidade padrão de registros por lote para evitar estouro de memória.
            
        Returns:
            Lista contendo os registros localizados para processamento.
        """
        query = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_by_user_and_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> Optional[JobApplication]:
        """
        Verifica se um determinado usuário já possui um vínculo com uma vaga específica.
        Previne a duplicação de candidaturas para uma mesma oportunidade de emprego.
        
        Args:
            user_id: ID único do usuário.
            job_id: ID único da vaga.
            
        Returns:
            A instância de JobApplication se o vínculo já existir, ou None caso contrário.
        """
        query = select(self.model).where(self.model.user_id == user_id, self.model.job_id == job_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()