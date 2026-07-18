"""
Job Hunter AI - Serviço de Vagas de Emprego
Orquestra as regras de negócio para ingestão, filtragem e atualização de vagas coletadas.
"""

from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.job_repository import JobRepository
from app.models.job import Job
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobService:
    """
    Classe de serviço responsável pelo gerenciamento de oportunidades de emprego.
    Garante a integridade dos dados coletados antes de enviá-los ao banco de dados.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o serviço injetando o repositório especializado de vagas."""
        self.job_repo = JobRepository(db_session=db_session)

    async def ingest_job(self, job_data: Dict[str, Any]) -> Optional[Job]:
        """
        Ingere uma nova vaga no sistema de forma idempotente.
        Verifica se a URL já existe no banco antes de criar um novo registro.
        
        Args:
            job_data: Dicionário contendo os dados brutos capturados pelo crawler.
            
        Returns:
            A instância do modelo Job criado, ou None se a vaga for duplicada.
        """
        url = job_data.get("url", "").strip()
        if not url:
            logger.warning("Job ingestion ignored: Missing source URL")
            return None

        # Garante a idempotência verificando se o link já foi processado anteriormente
        existing_job = await self.job_repo.get_by_url(url=url)
        if existing_job:
            logger.debug(f"Job ingestion skipped: URL already exists in database: {url}")
            return None

        logger.info(f"Ingesting new job from portal '{job_data.get('portal_source')}': {job_data.get('title')}")
        return await self.job_repo.create(obj_in_data=job_data)

    async def get_jobs_by_portal(self, portal: str, skip: int = 0, limit: int = 50) -> List[Job]:
        """Recupera uma lista paginada de vagas com base em um portal de origem específico."""
        return await self.job_repo.get_by_portal(portal_source=portal, skip=skip, limit=limit)

    async def get_job_by_id(self, job_id: uuid.UUID) -> Optional[Job]:
        """Busca uma vaga específica através do seu identificador único."""
        return await self.job_repo.get_by_id(id=job_id)

    async def update_structured_requirements(self, job_id: uuid.UUID, structured_requirements: Dict[str, Any]) -> Job:
        """
        Atualiza os requisitos estruturados da vaga processados por IA (Ex: stack, senioridade).
        Acionado pelo pipeline de processamento de contexto dos agentes.
        """
        db_obj = await self.job_repo.get_by_id(id=job_id)
        if not db_obj:
            logger.error(f"Job requirements update failed: target id {job_id} not found")
            raise ValueError("Oportunidade de emprego não localizada.")

        update_payload = {
            "structured_requirements": structured_requirements
        }

        logger.info(f"Updating job {job_id} with AI-extracted structured requirements")
        return await self.job_repo.update(db_obj=db_obj, obj_in_data=update_payload)