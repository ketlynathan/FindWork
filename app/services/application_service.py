"""
Job Hunter AI - Serviço de Candidaturas (Applications)
Orquestra as regras de negócio do funil de automação, scores e mudanças de estado.
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.application_repository import JobApplicationRepository
from app.models.application import JobApplication
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobApplicationService:
    """
    Classe de serviço responsável pelo controle do pipeline de candidaturas do usuário.
    Faz a interface entre os Agentes de IA, a fila de automação e a persistência.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o serviço injetando o repositório especializado de candidaturas."""
        self.app_repo = JobApplicationRepository(db_session=db_session)

    async def create_application(self, user_id: uuid.UUID, job_id: uuid.UUID, resume_id: uuid.UUID) -> JobApplication:
        """
        Inicia o vínculo de candidatura de um usuário com uma vaga de forma segura.
        Impede duplicidade se o usuário já tiver um processo ativo para a mesma vaga.
        
        Args:
            user_id: ID do usuário candidato.
            job_id: ID da vaga alvo.
            resume_id: ID da versão de currículo a ser utilizada.
            
        Returns:
            A instância de JobApplication criada.
            
        Raises:
            ValueError: Caso o usuário já tenha se candidatado a esta vaga anteriormente.
        """
        # Evita duplicidade de processos para o mesmo par Usuário-Vaga
        existing_app = await self.app_repo.get_by_user_and_job(user_id=user_id, job_id=job_id)
        if existing_app:
            logger.warning(f"Application rejected: User {user_id} already applied to job {job_id}")
            raise ValueError("Você já possui uma candidatura ou análise em andamento para esta vaga.")

        app_data = {
            "user_id": user_id,
            "job_id": job_id,
            "resume_id": resume_id,
            "status": "PENDING_ANALYSIS",  # Entra no topo do funil para o RankingAgent atuar
            "match_score": None,
            "match_rationale": None
        }

        logger.info(f"Initiating new application pipeline for user {user_id} on job {job_id}")
        return await self.app_repo.create(obj_in_data=app_data)

    async def update_ai_match_results(
        self, application_id: uuid.UUID, match_score: float, match_rationale: str, next_status: str = "WAITING_APPROVAL"
    ) -> JobApplication:
        """
        Atualiza os resultados de compatibilidade calculados pelo RankingAgent.
        
        Args:
            application_id: ID único da candidatura.
            match_score: Pontuação percentual de aderência.
            match_rationale: Justificativa detalhada gerada pela IA.
            next_status: Próximo estado do funil (padrão: aguardando aprovação do usuário).
        """
        db_obj = await self.app_repo.get_by_id(id=application_id)
        if not db_obj:
            logger.error(f"Application update failed: id {application_id} not found")
            raise ValueError("Candidatura não localizada no sistema.")

        update_payload = {
            "match_score": match_score,
            "match_rationale": match_rationale,
            "status": next_status
        }

        logger.info(f"Application {application_id} updated by RankingAgent. Score: {match_score}%")
        return await self.app_repo.update(db_obj=db_obj, obj_in_data=update_payload)

    async def update_status(self, application_id: uuid.UUID, status: str, error_logs: Optional[str] = None) -> JobApplication:
        """
        Atualiza o estado operacional da candidatura no funil de automação.
        Utilizado pelos robôs de submissão para atualizar o progresso ou registrar falhas.
        """
        db_obj = await self.app_repo.get_by_id(id=application_id)
        if not db_obj:
            logger.error(f"Status transitions failed: id {application_id} not found")
            raise ValueError("Candidatura não localizada.")

        update_payload = {"status": status}
        if error_logs is not None:
            update_payload["error_logs"] = error_logs

        logger.info(f"Transitioning application {application_id} status to '{status}'")
        return await self.app_repo.update(db_obj=db_obj, obj_in_data=update_payload)

    async def get_queue_by_status(self, status: str, batch_size: int = 20) -> List[JobApplication]:
        """Recupera uma lista de candidaturas filtradas por status para processamento em lote."""
        return await self.app_repo.get_by_status(status=status, limit=batch_size)

    async def get_user_dashboard_applications(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[JobApplication]:
        """Recupera o histórico completo de candidaturas do usuário ordenado por score."""
        return await self.app_repo.get_by_user_id(user_id=user_id, skip=skip, limit=limit)