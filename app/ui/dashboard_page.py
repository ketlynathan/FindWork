"""
Job Hunter AI - Painel de Controle Principal (UI Dashboard)
Apresenta indicadores de vagas, gerenciamento de perfil e gatilhos de triagem por IA.
"""

import asyncio
import streamlit as st
from app.services.user_service import UserService
from app.services.job_service import JobService
from app.ui.state import UIState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def render_dashboard_page():
    """
    Renderiza a visão geral do painel de controle do candidato,
    gerenciando estatísticas e o formulário de currículo/perfil técnico.
    """
    user_data = st.session_state.user_data
    if not user_data:
        st.warning("Sessão expirada ou usuário não identificado.")
        UIState.logout_user()
        return

    # Cabeçalho do Painel
    st.markdown(f"# 📈 Painel Geral — Bem-vindo, {user_data.get('name')}!")
    st.caption("Gerencie seus parâmetros profissionais e monitore a atividade dos seus agentes automáticos.")

    # Barra lateral simplificada para controle de logout e navegação
    with st.sidebar:
        st.markdown(f"**Logado como:**\n`{user_data.get('email')}`")
        if st.button("Explorar Vagas 🔍", use_container_width=True, type="primary"):
            st.session_state.current_page = "jobs_list"
            st.rerun()
        st.write("---")
        if st.button("Efetuar Logout 🚪", use_container_width=True):
            UIState.logout_user()

    # Executa consultas iniciais em lote de forma assíncrona para alimentar os gráficos e estatísticas
    async def _load_dashboard_data():
        async with UIState.get_db_context() as session:
            u_service = UserService(db_session=session)
            j_service = JobService(db_session=session)
            
            # Busca estado atualizado do perfil do usuário
            current_user = await u_service.get_user_by_id(user_data.get("id"))
            # Coleta métricas de contagem para os cards informativos
            metrics = await j_service.get_user_job_metrics(user_id=user_data.get("id"))
            
            return current_user, metrics

    try:
        db_user, metrics_data = asyncio.run(_load_dashboard_data())
    except Exception as e:
        logger.error("Failed to load dashboard state data vectors", error=str(e))
        st.error("Erro técnico ao carregar métricas do banco de dados.")
        return

    # 1. Seção de Indicadores Visuais (KPI Cards)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Vagas Coletadas", value=metrics_data.get("total", 0))
    with col2:
        st.metric(label="Vagas Recomendadas por IA", value=metrics_data.get("recommended", 0), delta="Aptas", delta_color="normal")
    with col3:
        st.metric(label="Oportunidades Descartadas", value=metrics_data.get("ignored", 0), delta="Inaptas", delta_color="inverse")

    st.write("---")

    # Organização do painel em Abas Funcionais
    tab_perfil, tab_triagem = st.tabs(["📝 Meu Perfil Profissional", "🤖 Central da IA (Triagem Manual)"])

    # ABA 1: Gerenciamento do Perfil Técnico do Usuário
    with tab_perfil:
        st.subheader("Seu Currículo & Preferências")
        st.markdown(
            "Cole abaixo seu resumo profissional detalhado, histórico de experiências, competências técnicas e linguagens. "
            "**O JobAgent utilizará este bloco exato de texto para julgar a sua afinidade com as vagas coletadas.**"
        )
        
        current_profile = db_user.resume_profile if db_user and db_user.resume_profile else ""
        
        # Campo de entrada de texto expansível para o perfil técnico
        profile_text = st.text_area(
            label="Perfil Técnico (Markdown ou texto puro)",
            value=current_profile,
            height=250,
            placeholder="Exemplo:\nDesenvolvedor Backend Python Sênior com 5 anos de experiência...\nSkills: FastAPI, Docker, PostgreSQL, AWS..."
        )
        
        if st.button("Salvar Meu Perfil", type="primary"):
            async def _update_profile():
                async with UIState.get_db_context() as session:
                    u_service = UserService(db_session=session)
                    return await u_service.update_user_profile(user_id=user_data.get("id"), new_profile=profile_text.strip())

            try:
                success = asyncio.run(_update_profile())
                if success:
                    st.success("Perfil profissional atualizado com sucesso!")
                else:
                    st.error("Não foi possível atualizar seu perfil.")
            except Exception as e:
                logger.error("Failed to update resume_profile from dashboard interface", error=str(e))
                st.error("Erro interno ao persistir dados do perfil.")

    # ABA 2: Acionamento Manual da Esteira de IA
    with tab_triagem:
        st.subheader("Processamento de Vagas Pendentes")
        st.markdown(
            "O agendador automático coleta vagas em segundo plano continuamente. "
            "Se você acabou de atualizar seu perfil ou deseja forçar a análise imediata de vagas que ainda não passaram pela IA, clique no botão abaixo."
        )
        
        if not current_profile:
            st.info("⚠️ Você precisa preencher e salvar seu Perfil Profissional antes de rodar a triagem de IA.")
        else:
            if st.button("🚀 Disparar Análise do JobAgent Agora", use_container_width=True):
                # Executa a esteira de análise em lote para o usuário logado
                async def _run_ai_pipeline():
                    async with UIState.get_db_context() as session:
                        j_service = JobService(db_session=session)
                        return await j_service.process_pending_jobs_for_user(user_id=user_data.get("id"))

                with st.spinner("O JobAgent está cruzando dados de vagas pendentes com seu currículo... Isso pode levar alguns segundos."):
                    try:
                        analyzed_count = asyncio.run(_run_ai_pipeline())
                        st.success(f"Triagem concluída! O agente de IA processou {analyzed_count} novas vagas com base no seu perfil.")
                        st.write("Dica: Clique em 'Explorar Vagas' na barra lateral para ver os resultados.")
                    except Exception as e:
                        logger.error("Fatal exception during manual UI trigger of JobAgent pipeline", error=str(e))
                        st.error("Ocorreu um erro durante a execução da esteira de IA. Verifique as credenciais da API do Gemini.")