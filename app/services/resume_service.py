"""
Job Hunter AI - Serviço de Currículos
Orquestra o upload, armazenamento físico e gerenciamento dos registros de currículos.
"""

import os
import uuid
from typing import List, Optional, Dict, Any
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.resume_repository import ResumeRepository
from app.models.resume import Resume
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ResumeService:
    """
    Classe de serviço responsável pelo ciclo de vida dos currículos dos candidatos.
    Gerencia o armazenamento físico dos PDFs e a integridade de persistência relacional.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o serviço injetando o repositório especializado de currículos."""
        self.resume_repo = ResumeRepository(db_session=db_session)
        # Define o diretório padrão de uploads seguro extraído das configurações globais
        self.upload_dir = getattr(settings, "UPLOAD_DIR", "storage/resumes")
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_resume_file(self, user_id: uuid.UUID, file_name: str, file_content: bytes) -> Resume:
        """
        Salva o arquivo físico do currículo em disco e cria o registro correspondente no banco.
        
        Args:
            user_id: Identificador único do usuário dono do currículo.
            file_name: Nome original do arquivo enviado (ex: 'meu_curriculo.pdf').
            file_content: Conteúdo binário (bytes) do arquivo PDF.
            
        Returns:
            A instância do modelo Resume criada e persistida no banco.
        """
        # Garante a geração de um nome único para o arquivo físico para evitar colisões no storage
        unique_file_id = uuid.uuid4()
        clean_ext = os.path.splitext(file_name)[1].lower() or ".pdf"
        stored_file_name = f"{user_id}_{unique_file_id}{clean_ext}"
        file_path = os.path.join(self.upload_dir, stored_file_name)

        logger.info(f"Saving physical resume file to storage: {file_path}")
        
        # Escrita assíncrona de arquivos para evitar o bloqueio do loop de eventos
        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(file_content)

        # Prepara os metadados iniciais para inserção na tabela 'resume'
        resume_data = {
            "user_id": user_id,
            "file_name": file_name,
            "file_path": file_path,
            "structured_data": {},  # Inicializa vazio; será preenchido pelo ResumeAgent
            "raw_text": None
        }

        logger.info(f"Creating database entry for user's {user_id} resume")
        return await self.resume_repo.create(obj_in_data=resume_data)

    async def get_user_resumes(self, user_id: uuid.UUID) -> List[Resume]:
        """Recupera o histórico completo de currículos de um usuário."""
        return await self.resume_repo.get_by_user_id(user_id=user_id)

    async def get_latest_resume(self, user_id: uuid.UUID) -> Optional[Resume]:
        """Recupera a versão ativa (mais recente) do currículo do candidato."""
        return await self.resume_repo.get_latest_by_user_id(user_id=user_id)

    async def update_structured_resume_data(self, resume_id: uuid.UUID, structured_data: Dict[str, Any], raw_text: str) -> Resume:
        """
        Atualiza o currículo com os dados extraídos e estruturados pela IA.
        Acionado diretamente pelo pipeline do ResumeAgent após o parsing.
        """
        db_obj = await self.resume_repo.get_by_id(id=resume_id)
        if not db_obj:
            logger.error(f"Resume context update failed: target id {resume_id} not found")
            raise ValueError("Currículo não localizado no sistema.")

        update_payload = {
            "structured_data": structured_data,
            "raw_text": raw_text
        }
        
        logger.info(f"Updating resume {resume_id} with AI-extracted metadata")
        return await self.resume_repo.update(db_obj=db_obj, obj_in_data=update_payload)