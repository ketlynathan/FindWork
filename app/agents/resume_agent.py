"""
Job Hunter AI - Agente Especialista em Análise de Currículos (ResumeAgent)
Faz a extração, normalização e estruturação de dados de perfis profissionais.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.services.resume_service import ResumeService
from app.utils.logger import get_logger

logger = get_logger(__name__)


# =====================================================================
# Schemas do Pydantic para Casamento Estrito de Dados (JSON Schema)
# =====================================================================

class WorkExperienceSchema(BaseModel):
    company: str = Field(..., description="Nome da empresa ou organização.")
    role: str = Field(..., description="Cargo ocupado pelo profissional.")
    start_date: str = Field(..., description="Data de início (ex: MM/AAAA ou Ano).")
    end_date: Optional[str] = Field(None, description="Data de término ou 'Atual'.")
    description: str = Field(..., description="Resumo das responsabilidades, conquistas e tecnologias utilizadas.")


class EducationSchema(BaseModel):
    institution: str = Field(..., description="Nome da faculdade, universidade ou escola técnica.")
    degree: str = Field(..., description="Curso ou grau acadêmico (ex: Bacharelado em Ciência da Computação).")
    status: str = Field(..., description="Situação atual: 'Concluído', 'Em andamento' ou 'Interrompido'.")
    end_year: Optional[str] = Field(None, description="Ano de conclusão previsto ou realizado.")


class StructuredResumeSchema(BaseModel):
    """Contrato final de dados que a LLM deve obrigatoriamente preencher."""
    full_name: str = Field(..., description="Nome completo do candidato.")
    headline: Optional[str] = Field(None, description="Título profissional curto (ex: Engenheiro de Software Senior).")
    summary: str = Field(..., description="Resumo profissional das competências gerais.")
    hard_skills: List[str] = Field(..., description="Lista de competências técnicas puras (ex: ['Python', 'SQL', 'Docker']).")
    soft_skills: List[str] = Field(..., description="Lista de competências comportamentais identificadas.")
    work_experiences: List[WorkExperienceSchema] = Field(default_factory=list, description="Histórico de trajetórias profissionais.")
    education: List[EducationSchema] = Field(default_factory=list, description="Histórico de formação acadêmica.")
    languages: List[str] = Field(default_factory=list, description="Idiomas falados e níveis de proficiência se houver.")


# =====================================================================
# Implementação do Agente Especialista
# =====================================================================

class ResumeAgent(BaseAgent):
    """
    Agente encarregado de ler currículos não estruturados e convertê-los 
    em modelos relacionais limpos baseados no StructuredResumeSchema.
    """

    def __init__(self, db_session: Any):
        """Inicializa o agente acoplando o serviço necessário para persistência."""
        super().__init__(temperature=0.1)  # Baixa temperatura para extração factual precisa
        self.resume_service = ResumeService(db_session=db_session)

    async def execute(self, resume_id: Any, raw_text: str) -> StructuredResumeSchema:
        """
        Orquestra a chamada de IA para estruturar o currículo e atualiza o banco de dados.
        
        Args:
            resume_id: ID do registro de currículo que foi armazenado.
            raw_text: Conteúdo textual extraído do arquivo PDF.
            
        Returns:
            Objeto StructuredResumeSchema preenchido.
        """
        logger.info(f"Starting AI parsing execution for resume: {resume_id}")

        system_prompt = (
            "Você é um sistema especialista em Recrutamento e Seleção (R&S) de alta performance. "
            "Sua tarefa é analisar o texto bruto de um currículo e extrair TODAS as informações relevantes, "
            "encaixando-as perfeitamente no esquema JSON solicitado.\n\n"
            "Diretrizes estritas:\n"
            "1. Não invente ou alucine dados. Se um campo não estiver presente ou implícito, deixe-o vazio ou nulo.\n"
            "2. Normalize as chaves de tecnologias no campo 'hard_skills' para termos limpos do mercado "
            "(ex: transformar 'conhecimento em linguagem Python' em apenas 'Python').\n"
            "3. Mantenha a descrição das experiências rica em detalhes, preservando conquistas citadas pelo candidato."
        )

        user_prompt = f"Aqui está o texto extraído do currículo para análise:\n\n--- TEXTO BRUTO ---\n{raw_text}\n-------------------"

        # Dispara a chamada estruturada usando o core do BaseAgent
        structured_output = await self._call_llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=StructuredResumeSchema
        )

        # Transforma o objeto do Pydantic em um dicionário nativo para salvar no campo JSONB do banco
        structured_dict = structured_output.model_dump()

        # Atualiza a persistência relacional com o texto bruto e os metadados da IA
        await self.resume_service.update_structured_resume_data(
            resume_id=resume_id,
            structured_data=structured_dict,
            raw_text=raw_text
        )

        logger.info(f"Resume {resume_id} successfully parsed and indexed into relational schema.")
        return structured_output