"""
Job Hunter AI - Agente Especialista em Análise de Vagas (JobAgent)
Extrai e padroniza requisitos, stacks e competências de oportunidades de emprego.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.services.job_service import JobService
from app.utils.logger import get_logger

logger = get_logger(__name__)


# =====================================================================
# Schemas do Pydantic para Estruturação da Vaga (JSON Schema)
# =====================================================================

class StructuredJobSchema(BaseModel):
    """Contrato de dados estruturados extraídos da descrição de uma vaga."""
    title: str = Field(..., description="Título limpo da vaga (ex: Engenheiro de Dados Pleno).")
    seniority: str = Field(..., description="Nível de senioridade inferido ou explícito: 'Júnior', 'Pleno', 'Sênior', 'Especialista' ou 'Não especificado'.")
    work_regime: str = Field(..., description="Regime de trabalho: 'Presencial', 'Híbrido', 'Remoto' ou 'Não especificado'.")
    required_hard_skills: List[str] = Field(..., description="Tecnologias, linguagens e ferramentas obrigatórias (ex: ['Python', 'AWS', 'Docker']).")
    desirable_hard_skills: List[str] = Field(default_factory=list, description="Conhecimentos desejáveis ou diferenciais citados na vaga.")
    soft_skills: List[str] = Field(default_factory=list, description="Competências comportamentais valorizadas na descrição (ex: ['Proatividade', 'Boa comunicação']).")
    salary_range: Optional[str] = Field(None, description="Faixa salarial informada (ex: 'R$ 8.000 - R$ 10.000') ou null se não mencionada.")
    benefits: List[str] = Field(default_factory=list, description="Lista de benefícios extraídos (ex: ['Vale Refeição', 'Plano de Saúde']).")


# =====================================================================
# Implementação do Agente Especialista
# =====================================================================

class JobAgent(BaseAgent):
    """
    Agente encarregado de normalizar e quebrar descrições de vagas
    em um modelo semântico estrito baseado no StructuredJobSchema.
    """

    def __init__(self, db_session: Any):
        """Inicializa o agente acoplando o serviço de vagas para persistência."""
        super().__init__(temperature=0.1)  # Baixa temperatura para manter a fidelidade técnica
        self.job_service = JobService(db_session=db_session)

    async def execute(self, job_id: Any, raw_description: str) -> StructuredJobSchema:
        """
        Orquestra a chamada de IA para mapear a vaga e atualiza o campo JSONB no banco.
        
        Args:
            job_id: ID do registro da vaga persistido no banco de dados.
            raw_description: Descrição ou texto completo extraído do portal de vagas.
            
        Returns:
            Objeto StructuredJobSchema com a stack e metadados devidamente mapeados.
        """
        logger.info(f"Starting AI structuring execution for job: {job_id}")

        system_prompt = (
            "Você é um Analista Técnico de Recrutamento (Tech Recruiter) auxiliado por IA. "
            "Sua tarefa é ler o texto descritivo de uma vaga e extrair com precisão a stack tecnológica, "
            "separando rigorosamente o que é obrigatório (required) do que é apenas diferencial ou desejável (desirable).\n\n"
            "Diretrizes:\n"
            "1. Normalize nomes de tecnologias para seus padrões de mercado (ex: 'JS' vira 'JavaScript', 'Postgres' vira 'PostgreSQL').\n"
            "2. Se a senioridade não estiver explícita no título ou texto, infira com base no tempo de experiência exigido "
            "ou complexidade das atividades (ex: exigência de arquitetura e liderança técnica aponta para Sênior).\n"
            "3. Não invente benefícios ou requisitos que não estejam textualmente suportados pela descrição."
        )

        user_prompt = f"Analise a seguinte descrição de vaga de emprego:\n\n--- DESCRIÇÃO DA VAGA ---\n{raw_description}\n------------------------"

        # Dispara a chamada estruturada aproveitando o mecanismo base do core
        structured_output = await self._call_llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=StructuredJobSchema
        )

        # Converte em dicionário primitivo para gravação direta no banco Postgres (coluna JSONB)
        structured_dict = structured_output.model_dump()

        # Atualiza o registro da vaga com o mapeamento semântico rico realizado pela LLM
        await self.job_service.update_structured_requirements(
            job_id=job_id,
            structured_requirements=structured_dict
        )

        logger.info(f"Job {job_id} requirements successfully structured and updated in storage.")
        return structured_output