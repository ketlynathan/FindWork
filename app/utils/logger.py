"""
Job Hunter AI - Logging Estruturado
Configura o structlog para fornecer telemetria rica e legível para crawlers e agentes.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from app.utils.config import get_settings

def configure_logger() -> None:
    """
    Configura globalmente o comportamento do structlog e do logging nativo do Python.
    Garante saídas colorizadas no terminal em dev e assinaturas limpas de eventos.
    """
    settings = get_settings()
    
    # Mapeamento do nível de log vindo das configurações para o padrão do módulo logging
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    selected_level = log_level_map.get(settings.LOG_LEVEL, logging.INFO)

    # Processadores compartilhados pelo structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.APP_ENV == "production":
        # Em produção, estruturamos os logs puramente como JSON para coletores de logs (ex: ELK, Grafana Loki)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Em desenvolvimento, usamos uma saída amigável, colorizada e tabulada no terminal
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configuração do Structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.BytesLoggerFactory() if settings.APP_ENV == "production" else structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(selected_level),
        cache_logger_on_first_use=True,
    )

    # Redireciona e intercepta os logs do logging nativo do Python (usado por libs como SQLAlchemy e Playwright)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=selected_level,
    )

    # Silencia logs excessivos de dependências externas para manter o terminal limpo
    logging.getLogger("pydantic").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Retorna um logger estruturado e contextualizado para o módulo específico.
    
    Args:
        name: O nome do contexto do logger (geralmente __name__).
    """
    return structlog.get_logger(name)