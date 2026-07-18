"""
Job Hunter AI - Agente Base Estrutural
Abstrai a comunicação com LLMs, tratamento de falhas e parametrização de prompts.
"""

from typing import Any, Dict, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """
    Classe abstrata que serve como fundação para a criação de Agentes Inteligentes.
    Gerencia de forma centralizada o cliente da API e chamadas resilientes à LLM.
    """

    def __init__(self, temperature: float = 0.2):
        """
        Inicializa o agente configurando o cliente assíncrono da OpenAI.
        
        Args:
            temperature: Grau de criatividade da LLM (padrão baixo para análise técnica estável).
        """
        if not settings.OPENAI_API_KEY:
            logger.critical("AI Agent initialization failed: OPENAI_API_KEY is missing")
            raise ValueError("Chave de API da OpenAI não configurada no ambiente.")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Método abstrato que força cada agente especialista a implementar sua própria lógica 
        de orquestração e execução de tarefas.
        """
        pass

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Executa uma chamada assíncrona padrão para a LLM com tratamento de exceções.
        
        Args:
            system_prompt: Instruções de comportamento e contexto do Agente.
            user_prompt: Entrada de dados variável (texto bruto, contexto).
            
        Returns:
            Resposta textual pura gerada pela LLM.
        """
        try:
            logger.debug(f"Dispatching standard LLM request to model: {self.model}")
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"LLM communication failure in {self.__class__.__name__}", error=str(e))
            raise RuntimeError(f"Falha na comunicação com o provedor de IA: {str(e)}")

    async def _call_llm_structured(self, system_prompt: str, user_prompt: str, response_model: Type[BaseModel]) -> BaseModel:
        """
        Executa uma chamada à LLM forçando o retorno de dados rigidamente estruturados 
        conforme um esquema Pydantic (Structured Outputs).
        
        Garante que a resposta siga um contrato JSON idêntico ao modelo esperado, 
        eliminando falhas de parsing nas camadas superiores.
        """
        try:
            logger.debug(f"Dispatching structured LLM request to model: {self.model}")
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=response_model
            )
            return response.choices[0].message.parsed
            
        except Exception as e:
            logger.error(f"Structured LLM communication failure in {self.__class__.__name__}", error=str(e))
            raise RuntimeError(f"Falha na geração de dados estruturados por IA: {str(e)}")