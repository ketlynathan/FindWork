# Auditoria de migração do protótipo Streamlit

O protótipo original continha uma boa intenção de domínio, incluindo agentes para estruturação de currículo, requisitos de vaga e aderência. Contudo, a aplicação não apresentava um fluxo funcional integral: o ponto de inicialização importava um agendador inexistente, a camada de interface chamava métodos que não estavam implementados nos serviços e havia divergências de nomes entre modelos, serviços e telas. A inicialização de banco também referenciava uma base ORM em caminho distinto do arquivo presente.

| Área | Situação no protótipo | Tratamento na aplicação web |
|---|---|---|
| Identidade | Login local desconectado da infraestrutura de produção | Autenticação integrada e procedures protegidas por usuário |
| Perfis | Um campo de perfil implícito e referências divergentes | Perfis completos, independentes e relacionados ao usuário autenticado |
| Vagas | Coleta e UI esperavam contratos diferentes | Base privada consolidada, filtros e requisitos estruturados |
| IA | Chave externa e chamadas sem proteção de fluxo | Agentes server-side com respostas estruturadas e sem expor credenciais |
| Candidatura | Estados previstos, mas sem revisão funcional | Rascunho, currículo adaptado, aprovação explícita e histórico auditável |
| Credenciais | Sem cofre ou regra de exibição | Central que não recebe, armazena ou mostra senhas no navegador |

A migração prioriza uma arquitetura publicável, com operações protegidas por usuário e uma trilha de aprovação obrigatória. Integrações reais com plataformas devem ser adicionadas somente por mecanismos oficiais ou autorizados; até essa conexão existir, a aplicação conduz a candidatura em modo assistido pelo link oficial.
