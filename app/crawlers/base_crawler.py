"""
Job Hunter AI - Crawler Base Estrutural
Abstrai conexões de rede assíncronas, gerenciamento de cabeçalhos e persistência de vagas.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import random
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.job_service import JobService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseCrawler(ABC):
    """
    Classe base abstrata para desenvolvimento de scrapers e crawlers de vagas.
    Centraliza o gerenciamento de requisições assíncronas e evasão de anti-bots básicos.
    """

    # Lista de User-Agents comuns para rotacionar e simular acessos legítimos
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    ]

    def __init__(self, db_session: AsyncSession):
        """
        Inicializa o crawler configurando o serviço de ingestão de vagas.
        
        Args:
            db_session: Sessão assíncrona do banco de dados para persistência direta.
        """
        self.job_service = JobService(db_session=db_session)
        # Timeout padrão robusto para evitar travamento em conexões lentas
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    @abstractmethod
    async def fetch_jobs(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Método abstrato para buscar e parsear vagas de um portal específico.
        Deve ser implementado obrigatoriamente por cada crawler especialista.
        """
        pass

    def _get_random_headers(self) -> Dict[str, str]:
        """Gera cabeçalhos HTTP simulando uma requisição vinda de um browser real."""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://google.com",
            "Referer": "https://google.com"
        }

    async def _send_request(
        self, method: str, url: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[httpx.Response]:
        """
        Encapsula o disparo de chamadas HTTP assíncronas com tratamento de falhas.
        
        Returns:
            Instância de httpx.Response se bem-sucedida, ou None em caso de erro.
        """
        # Utiliza o client do httpx em modo gerenciado para otimização de conexões (Connection Pooling)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                headers = self._get_random_headers()
                logger.debug(f"Dispatching {method} request to URL: {url}")
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    follow_redirects=True
                )
                
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error response code {e.response.status_code} matching URL {url}")
                return None
            except httpx.RequestError as e:
                logger.error(f"Network transport level connection failure targeting {url}", error=str(e))
                return None

    async def run(self, search_term: str, limit: int = 20) -> int:
        """
        Orquestrador de execução padrão do crawler.
        Coleta as vagas do portal parceiro e tenta ingeri-las no banco via JobService.
        
        Returns:
            Quantidade de novas vagas efetivamente inseridas (ignora duplicadas).
        """
        logger.info(f"Starting crawler cycle '{self.__class__.__name__}' for term: {search_term}")
        
        try:
            raw_jobs = await self.fetch_jobs(search_term=search_term, limit=limit)
        except Exception as e:
            logger.error(f"Fatal crash inside fetch_jobs execution tree of {self.__class__.__name__}", error=str(e))
            return 0

        inserted_count = 0
        for job_dict in raw_jobs:
            try:
                # O JobService internamente valida a URL e ignora se for repetida (idempotência)
                new_job = await self.job_service.ingest_job(job_data=job_dict)
                if new_job:
                    inserted_count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest individual job record during scraper streaming: {job_dict.get('title')}", error=str(e))

        logger.info(f"Crawler cycle '{self.__class__.__name__}' completed. New jobs added: {inserted_count}")
        return inserted_count