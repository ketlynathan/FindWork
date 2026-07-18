"""
Job Hunter AI - Repositório de Vagas de Emprego
Implementação do padrão Repository para operações na tabela 'job'.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository[Job]):
    """
    Repositório especializado para gerenciamento de vagas de emprego.
    Abstrai consultas complexas, paginações e checagens de integridade dos Crawlers.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o repositório vinculando explicitamente o modelo Job."""
        super().__init__(model=Job, db_session=db_session)

    async def get_by_url(self, url: str) -> Optional[Job]:
        """
        Busca uma vaga específica através da URL única do portal de origem.
        Utilizado pelos Crawlers para evitar inserções de registros duplicados.
        
        Args:
            url: Link completo da vaga.
            
        Returns:
            Instância de Job caso localizada, ou None se inédita.
        """
        query = select(self.model).where(self.model.url == url)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_portal(self, portal_source: str, skip: int = 0, limit: int = 50) -> List[Job]:
        """
        Recupera uma lista paginada de vagas com base em um portal de origem específico.
        
        Args:
            portal_source: Nome do portal coletor (ex: 'Gupy', 'LinkedIn').
            skip: Quantidade de registros a saltar (Paginação).
            limit: Quantidade máxima de registros a retornar.
            
        Returns:
            Lista contendo as vagas localizadas.
        """
        query = (
            select(self.model)
            .where(self.model.portal_source == portal_source)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())