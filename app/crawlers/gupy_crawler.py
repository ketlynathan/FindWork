"""
Job Hunter AI - Crawler Especialista para a Plataforma Gupy
Consome a API pública de busca da Gupy para capturar vagas de forma estruturada.
"""

from typing import Any, Dict, List
import urllib.parse
from app.crawlers.base_crawler import BaseCrawler
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GupyCrawler(BaseCrawler):
    """
    Crawler concreto encarregado de varrer e extrair oportunidades 
    diretamente do ecossistema de APIs públicas da Gupy.
    """

    BASE_API_URL = "https://portal.api.gupy.io/api/v1/jobs"

    async def fetch_jobs(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Consulta a API da Gupy buscando vagas pelo termo fornecido.
        
        Args:
            search_term: Palavra-chave de busca (ex: 'Desenvolvedor Python').
            limit: Quantidade máxima aproximada de registros a coletar.
            
        Returns:
            Lista de dicionários formatada no padrão da entidade Job.
        """
        # Codifica o termo para ser seguro para URLs (ex: converte espaços em %20)
        encoded_term = urllib.parse.quote(search_term)
        
        # Parâmetros padrão exigidos pela API da Gupy para busca pública
        params = {
            "searchTerm": encoded_term,
            "limit": min(limit, 100),  # Limita o tamanho do lote por requisição na API
            "offset": 0
        }

        logger.info(f"Requesting Gupy API payload for term '{search_term}'")
        response = await self._send_request(method="GET", url=self.BASE_API_URL, params=params)
        
        if not response:
            logger.warning("Empty or failed response returned from Gupy API endpoint")
            return []

        try:
            payload = response.json()
            # A Gupy envelopa os resultados dentro de uma chave chamada 'data'
            raw_jobs_list = payload.get("data", [])
        except Exception as e:
            logger.error("Failed to parse JSON payload returned from Gupy gateway", error=str(e))
            return []

        parsed_jobs: List[Dict[str, Any]] = []

        for raw_job in raw_jobs_list:
            # Filtra e extrai apenas os campos cruciais mapeando para o nosso schema de banco
            job_id = raw_job.get("id")
            job_url = raw_job.get("jobUrl") or f"https://vagas.gupy.io/jobs/{job_id}"

            # Monta a localização física da vaga
            city = raw_job.get("city") or ""
            state = raw_job.get("state") or ""
            location_str = f"{city} - {state}" if city and state else (city or state or "Remoto/Não informado")

            # Mapeamento e normalização dos dados coletados
            job_mapped = {
                "title": raw_job.get("name", "Vaga sem título").strip(),
                "company_name": raw_job.get("companyName", "Empresa Confidencial").strip(),
                "location": location_str,
                "description": raw_job.get("description", "").strip(),
                "url": job_url.strip(),
                "portal_source": "Gupy",
                "structured_requirements": {},  # Deixado em branco para o JobAgent processar depois
                "is_active": True
            }

            # Incrementa opcionalmente os pré-requisitos fornecidos pela própria plataforma se existirem
            prerequisites = raw_job.get("prerequisites", "")
            if prerequisites and job_mapped["description"]:
                job_mapped["description"] += f"\n\n--- REQUISITOS ADICIONAIS ---\n{prerequisites}"

            parsed_jobs.append(job_mapped)

        logger.info(f"Successfully filtered and parsed {len(parsed_jobs)} raw jobs from Gupy")
        return parsed_jobs