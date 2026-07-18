"""
Job Hunter AI - Agente de Triagem e Afinidade (RankingAgent)
Mapeia a aderência de competências e gera relatórios de tomada de decisão.
"""

from typing import List, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.services.application_service import JobApplicationService
from app.utils.logger import get_logger

logger = get_logger(__name__)


# =====================================================================
# Schemas do Pydantic para o Relatório de Afinidade (JSON Schema)
# =====================================================================

class RankingAnalysisSchema(BaseModel):
    """Contrato do relatório técnico de aderência gerado pelo RankingAgent."""
    match_score: float = Field(..., description="Pontuação percentual realista de aderência (0.0 a 100.0) calculada com rigor.")
    strong_points: List[str] = Field(..., description="Pontos fortes do candidato que dão match exato com os requisitos da vaga.")
    gaps: List[str] = Field(..., description="Tecnologias ou competências obrigatórias exigidas na vaga que faltam no perfil do candidato.")
    interview_tips: List[str] = Field(..., description="Dicas estratégicas do que o candidato deve enfatizar ou revisar para as entrevistas.")
    summary_rationale: str = Field(..., description="Justificativa analítica curta explicando o motivo da nota concedida.")


# =====================================================================
# Implementação do Agente Especialista
# =====================================================================

class RankingAgent(BaseAgent):
    """
    Agente encarregado de julgar a afinidade técnica e comportamental,
    alimentando os indicadores de sucesso da esteira automatizada.
    """

    def __init__(self, db_session: Any):
        """Inicializa o agente injetando o serviço de candidaturas para persistência."""
        super().__init__(temperature=0.1)  # Alta estabilidade analítica
        self.app_service = JobApplicationService(db_session=db_session)

    async def execute(self, application_id: Any, structured_resume: dict, structured_job: dict) -> RankingAnalysisSchema:
        """
        Calcula o casamento de dados entre o currículo e a vaga e salva o veredito no banco.
        
        Args:
            application_id: ID do registro da candidatura a ser atualizado.
            structured_resume: Dicionário contendo os dados estruturados do currículo (JSONB).
            structured_job: Dicionário contendo os requisitos estruturados da vaga (JSONB).
            
        Returns:
            Objeto contendo a análise profunda de aderência (RankingAnalysisSchema).
        """
        logger.info(f"Executing AI match making for application: {application_id}")

        system_prompt = (
            "Você é um Headhunter Técnico Sênior encarregado de ranquear candidatos para posições de engenharia e tecnologia. "
            "Sua missão é realizar uma comparação minuciosa entre o Perfil Estruturado do Candidato e os Requisitos Estruturados da Vaga.\n\n"
            "Diretrizes para o cálculo do 'match_score':\n"
            "1. Seja criterioso e realista. Não infle notas. Um match de 100% exige todas as tecnologias obrigatórias e senioridade compatível.\n"
            "2. Penalize caso tecnologias obrigatórias ('required_hard_skills') da vaga estejam ausentes nas competências do candidato.\n"
            "3. Habilidades desejáveis ('desirable_hard_skills') servem como bônus e não devem derrubar a nota se estiverem ausentes.\n"
            "4. Avalie o nível de senioridade. Um candidato júnior aplicando para vaga sênior deve receber uma nota severamente baixa."
        )

        user_prompt = (
            f"--- DADOS DO CANDIDATO ---\n{structured_resume}\n\n"
            f"--- REQUISITOS DA VAGA ---\n{structured_job}\n\n"
            f"Realize o cruzamento e gere o relatório técnico de afinidade."
        )

        # Solicita à LLM a geração do output rigidamente estruturado
        analysis_result = await self._call_llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=RankingAnalysisSchema
        )

        # Prepara a justificativa textual formatada em Markdown para melhor leitura na interface
        compiled_rationale = (
            f"### Resumo do Match\n{analysis_result.summary_rationale}\n\n"
            f"#### Pontos Fortes 👍\n" + "\n".join([f"- {p}" for p in analysis_result.strong_points]) + "\n\n"
            f"#### Lacunas Identificadas ⚠️\n" + "\n".join([f"- {g}" for g in analysis_result.gaps]) + "\n\n"
            f"#### Preparação para a Entrevista 💡\n" + "\n".join([f"- {t}" for t in analysis_result.interview_tips])
        )

        # Atualiza a linha de candidatura com a nota, relatório e move para a aprovação do usuário
        await self.app_service.update_ai_match_results(
            application_id=application_id,
            match_score=analysis_result.match_score,
            match_rationale=compiled_rationale,
            next_status="WAITING_APPROVAL"
        )

        logger.info(f"Application {application_id} analysis completed. Final score: {analysis_result.match_score}%")
        return analysis_result