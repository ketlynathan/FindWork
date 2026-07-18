"""
Job Hunter AI - Tela de Listagem e Exploração de Vagas (UI)
Apresenta as vagas coletadas com os pareceres de inteligência artificial aplicados.
"""

import asyncio
import streamlit as st
from app.services.job_service import JobService
from app.ui.state import UIState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def render_jobs_list_page():
    """
    Renderiza a interface de pesquisa, listagem e detalhamento de vagas filtradas por usuário.
    """
    user_data = st.session_state.user_data
    if not user_data:
        st.warning("Sessão inválida.")
        UIState.logout_user()
        return

    st.markdown("# 🔍 Oportunidades Triadas por IA")
    st.caption("Explore a lista completa de vagas coletadas e veja quais dão 'match' com seu perfil profissional.")

    # Barra lateral para controle de navegação de volta ao painel
    with st.sidebar:
        st.markdown(f"**Candidato:**\n`{user_data.get('email')}`")
        if st.button("Voltar ao Painel 📈", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()

    # --- Filtros de Interface ---
    col_filtro, col_busca = st.columns([1, 2])
    
    with col_filtro:
        recommendation_filter = st.selectbox(
            "Filtrar por recomendação da IA:",
            options=["Todas", "Apenas Recomendadas (Aptas)", "Apenas Ignoradas (Inaptas)", "Não Avaliadas"],
            index=0
        )
        
    with col_busca:
        search_query = st.text_input("Buscar por palavra-chave (Título ou Empresa):", placeholder="Ex: Engenheiro, São Paulo, Home Office...")

    # Mapeia a seleção do selectbox para os parâmetros booleanos aceitos pelo Repositório
    is_recommended = None
    if recommendation_filter == "Apenas Recomendadas (Aptas)":
        is_recommended = True
    elif recommendation_filter == "Apenas Ignoradas (Inaptas)":
        is_recommended = False

    # Executa a busca assíncrona com os critérios preenchidos pelo usuário na tela
    async def _fetch_jobs():
        async with UIState.get_db_context() as session:
            j_service = JobService(db_session=session)
            return await j_service.list_jobs_for_ui(
                user_id=user_data.get("id"),
                is_recommended=is_recommended,
                search_query=search_query.strip() if search_query else None,
                limit=50
            )

    with st.spinner("Buscando vagas no banco de dados..."):
        try:
            jobs = asyncio.run(_fetch_jobs())
        except Exception as e:
            logger.error("Error fetching jobs from list page query stream", error=str(e))
            st.error("Falha ao carregar lista de vagas.")
            return

    # --- Renderização dos Resultados ---
    if not jobs:
        st.info("Nenhuma vaga encontrada para os filtros selecionados ou nenhuma vaga foi coletada ainda.")
        return

    st.write(f"Exibindo as **{len(jobs)}** vagas mais recentes encontradas:")

    for job, analysis in jobs:
        # Define uma tag visual baseada no estado da análise de IA
        if analysis:
            if analysis.is_recommended:
                badge = "🟢 **RECOMENDADA (APTA)**"
                match_score = f"📊 Afinidade: **{analysis.match_score}/100**"
            else:
                badge = "🔴 *IGNORADA (INAPTA)*"
                match_score = f"📊 Afinidade: **{analysis.match_score}/100**"
        else:
            badge = "🟡 *AGUARDANDO ANÁLISE*"
            match_score = "📊 Afinidade: *N/A*"

        # Título do elemento expansível (Card da Vaga)
        card_title = f"[{job.platform.upper()}] {job.title} — {job.company or 'Empresa Oculta'} ({job.location or 'Remoto'})"
        
        with st.expander(f"{badge} | {card_title}"):
            st.markdown(f"### {job.title}")
            st.write(f"**Empresa:** {job.company or 'Não informada'} | **Localização:** {job.location or 'Não informada'}")
            st.write(f"**Link Original da Vaga:** [{job.url}]({job.url})")
            st.write("---")
            
            # Divide o espaço interno entre Detalhes Técnicos e Parecer da IA
            col_desc, col_ia = st.columns([1, 1])
            
            with col_desc:
                st.markdown("#### 📋 Descrição da Vaga")
                # Limita a descrição longa para não quebrar o layout, permitindo leitura completa se necessário
                if job.description:
                    st.text_area("Texto original:", value=job.description, height=250, disabled=True, key=f"desc_{job.id}")
                else:
                    st.write("*Descrição não fornecida.*")
                    
            with col_ia:
                st.markdown(f"#### 🤖 Avaliação da Inteligência Artificial")
                st.markdown(match_score)
                
                if analysis:
                    # Renderiza a justificativa estruturada vinda do banco
                    st.markdown("**Justificativa do Agente:**")
                    st.info(analysis.justification)
                    st.caption(f"Analisado em: {analysis.analyzed_at.strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.warning("Esta vaga ainda não foi processada pelo JobAgent. Vá até o **Painel Geral** e clique em **Disparar Análise** na central da IA para processá-la.")