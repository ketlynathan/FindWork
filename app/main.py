"""
Job Hunter AI - Arquivo Principal de Inicialização (Main Entrypoint)
Orquestra o ciclo de vida do banco, agendador em background e roteamento da UI Streamlit.
"""
import sys
import os
# Adiciona a pasta pai ao caminho de busca do Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import threading
import streamlit as st
from app.database.session import init_db
from app.scheduler.worker import start_scheduler_background_thread
from app.ui.state import UIState
from app.ui.login_page import render_login_page
from app.ui.dashboard_page import render_dashboard_page
from app.ui.jobs_list_page import render_jobs_list_page
from app.utils.logger import get_logger

logger = get_logger(__name__)


def initialize_application():
    """
    Executa a rotina crítica de boot da aplicação.
    Garante inicialização única do banco de dados e do agendador em background.
    """
    # Usamos o st.cache_resource para garantir que este bloco rode APENAS UMA VEZ
    # durante todo o ciclo de vida do servidor Streamlit, evitando concorrência ou travas.
    @st.cache_resource
    def _bootstrap():
        logger.info("Initializing system core components...")
        
        # 1. Cria as tabelas do SQLite se elas não existirem
        init_db()
        logger.info("Database schemas validated/created successfully.")
        
        # 2. Inicializa o agendador de raspagem e triagem automática em uma Thread separada
        start_scheduler_background_thread()
        logger.info("Background job scraping scheduler spawned successfully.")
        
        return True

    _bootstrap()


def main():
    """
    Orquestrador e roteador principal da interface gráfica.
    """
    # Configurações básicas da página no navegador (deve ser o primeiro comando Streamlit)
    st.set_page_config(
        page_title="Job Hunter AI",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 1. Roda a inicialização do Core (Banco + Scheduler)
    initialize_application()

    # 2. Inicializa as chaves do Session State da UI de forma defensiva
    UIState.init_session_state()

    # 3. Roteador de Telas (Engine SPA)
    current_page = st.session_state.current_page

    if not st.session_state.authenticated:
        # Se não estiver autenticado, força a renderização da tela de Login/Cadastro
        render_login_page()
    else:
        # Roteamento baseado no estado dinâmico gerenciado pelos botões das páginas
        if current_page == "dashboard":
            render_dashboard_page()
        elif current_page == "jobs_list":
            render_jobs_list_page()
        else:
            # Fallback de segurança caso o estado quebre
            st.session_state.current_page = "dashboard"
            st.rerun()


if __name__ == "__main__":
    main()