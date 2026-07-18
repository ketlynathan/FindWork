"""
Job Hunter AI - Gerenciador de Estado da UI (Streamlit Session State)
Centraliza o controle de sessão, autenticação e instâncias de serviço globais.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import streamlit as st
from app.database.session import db_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UIState:
    """
    Controlador estático do ciclo de vida e estado da interface gráfica.
    Garante persistência de dados entre as re-execuções nativas do Streamlit.
    """

    @staticmethod
    def init_session_state():
        """
        Inicializa todas as chaves obrigatórias do dicionário de estado.
        Deve ser invocado logo no topo do arquivo principal (main.py).
        """
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
            
        if "user_data" not in st.session_state:
            st.session_state.user_data = None  # Armazena ID, nome e e-mail do usuário logado
            
        if "access_token" not in st.session_state:
            st.session_state.access_token = None
            
        if "current_page" not in st.session_state:
            st.session_state.current_page = "login"  # Controle de roteamento de páginas internas

    @staticmethod
    def login_user(auth_payload: dict):
        """
        Injeta o payload de autenticação gerado pelo UserService no estado da aplicação.
        
        Args:
            auth_payload: Dicionário contendo 'user' e 'access_token'.
        """
        st.session_state.authenticated = True
        st.session_state.user_data = auth_payload.get("user")
        st.session_state.access_token = auth_payload.get("access_token")
        st.session_state.current_page = "dashboard"
        logger.info(f"UI State updated: User {st.session_state.user_data.get('id')} logged in.")

    @staticmethod
    def logout_user():
        """Limpa as credenciais de segurança e joga o usuário de volta para a tela de login."""
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.access_token = None
        st.session_state.current_page = "login"
        logger.info("UI State updated: User logged out successfully.")
        st.rerun()

    @staticmethod
    @asynccontextmanager
    async def get_db_context() -> AsyncGenerator:
        """
        Gerenciador de contexto assíncrono para operações de banco dentro da UI.
        Garante que a sessão seja fechada corretamente mesmo em caso de erros de renderização.
        
        Yields:
            AsyncSession: Uma sessão ativa com o banco de dados.
        """
        async with db_session() as session:
            try:
                yield session
            except Exception as e:
                logger.error("Database transaction failure inside UI layer context", error=str(e))
                raise e