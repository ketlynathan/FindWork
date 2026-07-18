"""
Job Hunter AI - Agendador de Tarefas em Segundo Plano (Background Scheduler)
Gerencia a execução cíclica e assíncrona de crawlers e agentes de IA.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database.session import db_session
from app.crawlers.gupy_crawler import GupyCrawler
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instancia o agendador assíncrono global focado no loop de eventos do asyncio
scheduler = AsyncIOScheduler()


async def execute_job_scraping_cycle():
    """
    Trabalhador (Worker) assíncrono que abre uma sessão curta com o banco de dados
    e dispara a esteira de coleta de novas vagas de emprego.
    """
    logger.info("Background worker initiated: Job scraping cycle triggered.")
    
    # Abre um contexto de sessão assíncrona isolado para a execução desta thread/rotina
    async with db_session() as session:
        try:
            crawler = GupyCrawler(db_session=session)
            
            # Termos padrão de busca para alimentar o ecossistema (pode ser customizado ou dinâmico)
            search_terms = ["Python", "Desenvolvedor", "Engenharia de Dados", "React"]
            
            total_added = 0
            for term in search_terms:
                # Executa a coleta de até 30 vagas por termo
                added_count = await crawler.run(search_term=term, limit=30)
                total_added += added_count
                
            # Confirma a transação em lote se tudo correr bem
            await session.commit()
            logger.info(f"Background scraping cycle completed successfully. Total new jobs added: {total_added}")
            
        except Exception as e:
            # Em caso de qualquer falha catastrófica, desfaz alterações pendentes para não corromper a sessão
            await session.rollback()
            logger.error("Fatal error during background job scraping cycle transaction", error=str(e))


def start_scheduler():
    """
    Inicializa o agendador e registra as tarefas periódicas (Jobs).
    Deve ser invocado na inicialização do servidor ou do worker principal.
    """
    if scheduler.running:
        logger.warning("Scheduler start requested, but it is already running.")
        return

    logger.info("Initializing Job Hunter AI Background Scheduler...")

    # Agenda a rotina de raspagem para rodar a cada 60 minutos
    scheduler.add_job(
        execute_job_scraping_cycle,
        trigger=IntervalTrigger(minutes=60),
        id="gupy_scraping_job",
        name="Varrer vagas na plataforma Gupy periodicamente",
        replace_existing=True
    )

    # Inicia o loop de monitoramento em segundo plano de forma não-bloqueante
    scheduler.start()
    logger.info("Background Scheduler successfully started and listening.")


def shutdown_scheduler():
    """
    Desliga o agendador de forma limpa, aguardando a conclusão de tarefas em execução.
    """
    if scheduler.running:
        logger.info("Stopping background scheduler graciosamente...")
        scheduler.shutdown(wait=True)
        logger.info("Background Scheduler stopped.")