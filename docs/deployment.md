# Publicação do FindWork

## Validação concluída

A aplicação foi validada com verificação estática de TypeScript, suíte de testes com oito casos aprovados e revisão visual das cinco telas principais em desktop e celular. A revisão confirmou navegação responsiva, formulários, estados vazios e a hierarquia visual do painel.

A build de produção foi gerada com sucesso. O empacotador reportou apenas um alerta não bloqueante de tamanho de arquivo JavaScript; a aplicação continua pronta para publicação, e a divisão adicional de código pode ser considerada em uma evolução posterior caso o produto cresça.

| Verificação | Resultado |
|---|---|
| Tipos TypeScript | Aprovado com `pnpm check` |
| Testes automatizados | Aprovado com `pnpm test` — 8 testes |
| Isolamento por usuário | Coberto nas procedures e nos acessos de banco por `userId` |
| Regra de aprovação | Bloqueada antes do registro de envio |
| Currículo adaptado | Com prompt restritivo, controle de afirmações excluídas e revisão humana |
| Desktop e celular | Revisados nas rotas de painel, perfis, oportunidades, candidaturas e integrações |

## Opção recomendada: publicação gerenciada

Use a publicação disponível no painel do projeto após criar um checkpoint. Essa opção preserva a autenticação, o banco, o armazenamento protegido de currículos e as variáveis de ambiente já configuradas para a aplicação.

## Vercel ou Netlify

O código é uma aplicação React/Vite com servidor Express e procedures tRPC. É possível hospedá-lo em Vercel ou Netlify, mas a migração precisa substituir ou reconfigurar as dependências gerenciadas: autenticação, banco de dados, armazenamento de currículos e credenciais server-side de IA.

| Plataforma | Ajustes necessários | Observação |
|---|---|---|
| Vercel | Adaptar o servidor Express para funções/rotas de servidor, fornecer banco externo, armazenamento compatível e variáveis de ambiente seguras | Adequada quando a equipe já usa Vercel e mantém a infraestrutura complementar |
| Netlify | Adaptar procedures para funções serverless, fornecer banco externo, armazenamento compatível e variáveis de ambiente seguras | Adequada quando a equipe já centraliza sites e funções em Netlify |
| Publicação gerenciada | Nenhuma adaptação de infraestrutura para os componentes já configurados | Recomendação para a primeira versão operacional |

Em qualquer opção, nunca inclua senhas, tokens de plataformas de vagas ou chaves de IA no código-fonte, no cliente ou em repositórios. Guarde segredos somente no gerenciador de variáveis do provedor escolhido e implemente conexões oficiais ou autorizadas por servidor.
