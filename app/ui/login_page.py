"""
Job Hunter AI - Tela de Autenticação e Registro (UI)
Gerencia os formulários visuais de login e cadastro integrado ao UserService.
"""

import asyncio
import streamlit as st
from app.services.user_service import UserService
from app.ui.state import UIState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def render_login_page():
    """
    Renderiza os formulários de autenticação.
    Alterna dinamicamente entre Login e Cadastro usando o st.session_state.
    """
    # Inicializa uma chave temporária para alternar a aba de visualização interna
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    st.markdown("<h1 style='text-align: center;'>🎯 Job Hunter AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Sua esteira inteligente de monitoramento e aplicação de vagas com IA</p>", unsafe_allow_html=True)
    st.write("---")

    # Centraliza o formulário na tela criando 3 colunas (foco na coluna do meio)
    _, col_centro, _ = st.columns([1, 2, 1])

    with col_centro:
        if st.session_state.auth_mode == "login":
            st.subheader("Acesse sua Conta")
            
            email = st.text_input("E-mail", placeholder="seu.email@exemplo.com", key="login_email")
            password = st.text_input("Senha", type="password", placeholder="••••••••", key="login_password")
            
            if st.button("Entrar", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                else:
                    # Executa a chamada assíncrona de autenticação
                    async def _handle_login():
                        async with UIState.get_db_context() as session:
                            user_service = UserService(db_session=session)
                            return await user_service.authenticate_user(email=email.strip(), password=password)

                    try:
                        auth_payload = asyncio.run(_handle_login())
                        if auth_payload:
                            st.success("Autenticação bem-sucedida!")
                            UIState.login_user(auth_payload)
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas. Verifique seu e-mail e senha.")
                    except Exception as e:
                        logger.error("Failed executing UI login action", error=str(e))
                        st.error("Ocorreu um erro interno ao tentar realizar o login.")

            st.write("")
            if st.button("Não tem uma conta? Cadastre-se aqui", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()

        else:
            st.subheader("Criar Nova Conta")
            
            name = st.text_input("Nome Completo", placeholder="João Silva", key="reg_name")
            email = st.text_input("E-mail", placeholder="seu.email@exemplo.com", key="reg_email")
            password = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="reg_password")
            
            if st.button("Finalizar Cadastro", use_container_width=True, type="primary"):
                if not name or not email or not password:
                    st.error("Por favor, preencha todos os campos obrigatórios.")
                elif len(password) < 6:
                    st.error("A senha deve conter no mínimo 6 caracteres.")
                else:
                    # Executa a chamada assíncrona de cadastro de usuário
                    async def _handle_registration():
                        async with UIState.get_db_context() as session:
                            user_service = UserService(db_session=session)
                            return await user_service.register_user(name=name.strip(), email=email.strip(), password=password)

                    try:
                        new_user = asyncio.run(_handle_registration())
                        if new_user:
                            st.success("Conta criada com sucesso! Faça login para continuar.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error("Este e-mail já está cadastrado no sistema.")
                    except Exception as e:
                        logger.error("Failed executing UI registration action", error=str(e))
                        st.error("Ocorreu um erro ao processar seu cadastro.")

            st.write("")
            if st.button("Já possui uma conta? Voltar para o Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()