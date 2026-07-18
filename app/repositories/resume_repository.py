"""
Job Hunter AI - Repositório de Currículos
Implementação do padrão Repository para operações na tabela 'resume'.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import Resume
from app.repositories.base_repository import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    """
    Repositório especializado para gerenciamento de dados de currículos.
    Abstrai consultas complexas e regras de persistência da entidade Resume.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o repositório vinculando explicitamente o modelo Resume."""
        super().__init__(model=Resume, db_session=db_session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[Resume]:
        """
        Recupera todos os currículos associados a um usuário específico.
        Utilizado para listar o histórico de uploads do candidato na interface.
        
        Args:
            user_id: ID único (UUID) do usuário dono dos currículos.
            
        Returns:
            Lista contendo os currículos localizados.
        """
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc())
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_user_id(self, user_id: uuid.UUID) -> Optional[Resume]:
        """
        Recupera o currículo mais recente enviado pelo usuário.
        Utilizado como padrão pelo sistema nas rotinas de candidatura e comparação de vagas.
        
        Args:
            user_id: ID único (UUID) do usuário.
            
        Returns:
            Instância do Resume mais recente ou None se o usuário não tiver uploads.
        """
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()