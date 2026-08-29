# Project TODO

- [x] Documentar a auditoria do protótipo Streamlit e os desvios funcionais corrigidos pela migração.
- [x] Modelar dados isolados por usuário para perfis profissionais, currículos, preferências, vagas, análises, candidaturas e integrações.
- [x] Implementar autenticação com proteção de todas as operações de leitura e escrita por usuário.
- [x] Cadastrar e editar perfis profissionais independentes, incluindo área, senioridade, competências, currículo, regiões e modalidades desejadas.
- [x] Implementar armazenamento seguro de currículo e seleção de uma versão ativa por perfil profissional.
- [x] Implementar catálogo pesquisável de vagas com filtros por região, área, palavra-chave, modalidade e perfil escolhido.
- [x] Implementar agente analista para estruturar requisitos, modalidade, senioridade e competências de cada vaga.
- [x] Implementar agente recrutador para calcular aderência, lacunas, justificativa e prioridade por perfil.
- [x] Implementar adaptação de currículo específica por vaga sem inventar experiências, competências ou conquistas.
- [x] Implementar fluxo de candidatura assistida com revisão, aprovação explícita, estados, links e histórico auditável.
- [x] Bloquear qualquer ação de candidatura sem registro explícito de aprovação do usuário.
- [x] Implementar central de integrações que armazene apenas referências e metadados de conexão, sem exibir senhas.
- [x] Priorizar integrações oficiais ou autorizadas e deixar automações de plataformas não conectadas em modo assistido.
- [x] Construir painel elegante com recomendações, funil de candidaturas e atividade dos agentes.
- [x] Aplicar uma experiência responsiva, acessível e visualmente coesa em todas as telas.
- [x] Criar testes de regras críticas, especialmente isolamento de dados, candidatura aprovada e adaptação fiel do currículo.
- [x] Executar validação técnica, revisão visual e preparar instruções objetivas de publicação em Vercel e Netlify.

- [ ] Corrigir o diretório raiz e o comando de instalação do Vercel para localizar o package.json e respeitar o lockfile do projeto.
- [ ] Validar a configuração de build do Vercel e documentar que o backend Express/tRPC ainda requer adaptação para Functions.

- [x] Criar uma referência arquivada do protótipo Streamlit no GitHub.
- [x] Copiar a versão web migrada para o repositório GitHub sem levar segredos, caches ou artefatos de build.
- [x] Criar commit e enviar a versão web migrada para o GitHub, validando o resultado.
