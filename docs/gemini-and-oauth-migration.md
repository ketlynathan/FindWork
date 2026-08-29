# Migração de IA para Gemini e autenticação no Vercel

## 1. Arquivos atuais que utilizam IA

| Arquivo | Uso atual | Alteração necessária |
|---|---|---|
| `server/_core/llm.ts` | Cliente genérico OpenAI-compatible que envia requests ao Forge usando `ENV.forgeApiUrl` e `ENV.forgeApiKey`. Também normaliza mensagens, schemas JSON, retries e respostas. | Substituir pelo adaptador Gemini ou criar `server/_core/gemini.ts` com `GEMINI_API_KEY` server-side. A camada de retry pode ser reaproveitada, mas o payload e a leitura da resposta devem seguir Gemini. |
| `server/careerAgents.ts` | Implementa `analyzeJobRequirements`, `evaluateFit` e `tailorResume`. Todos chamam `invokeLLM`, usam `gpt-5-mini` e enviam JSON Schema no formato OpenAI-compatible. | Trocar `invokeLLM` por `invokeGeminiJson`, trocar o modelo por um modelo Gemini aprovado e converter `response_format` para `responseMimeType: application/json` + `responseSchema` ou para a configuração equivalente do SDK `@google/genai`. |
| `server/routers/career.ts` | Chama os três agentes nas procedures protegidas `jobs.analyze`, `jobs.match` e `jobs.adaptAndDraft`. | Não deve receber a chave. Continua sendo a fronteira autenticada que chama os agentes server-side. Pode apenas atualizar mensagens de erro e observabilidade. |
| `server/_core/env.ts` | Lê as variáveis server-side atuais, incluindo `BUILT_IN_FORGE_API_KEY`. | Adicionar `geminiApiKey: process.env.GEMINI_API_KEY ?? ""`. Esse objeto só deve ser importado por código do servidor. |
| `client/src/pages/OpportunitiesPage.tsx` | Dispara as procedures tRPC e exibe resultados. | Não importar Gemini, não ler `GEMINI_API_KEY` e não fazer chamadas diretas ao Google. Nenhuma alteração de chave é necessária no frontend. |

## 2. Estratégia recomendada para Gemini

A opção mais limpa é criar um adaptador server-side, por exemplo `server/_core/gemini.ts`, e deixar `server/careerAgents.ts` independente do fornecedor. A chave deve ser lida somente com `process.env.GEMINI_API_KEY` ou através de `ENV.geminiApiKey` no servidor.

O Google recomenda variáveis de ambiente para as chaves e alerta que uma chave compilada no cliente pode ser extraída e utilizada por terceiros. O frontend deve chamar apenas as procedures tRPC autenticadas do FindWork [1].

Exemplo conceitual usando o SDK oficial atual:

```ts
// server/_core/gemini.ts — nunca importar este arquivo no client/
import { GoogleGenAI } from "@google/genai";

const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) throw new Error("GEMINI_API_KEY não configurada no servidor");

const ai = new GoogleGenAI({ apiKey });

export async function invokeGeminiJson<T>(input: {
  model: string;
  system: string;
  user: string;
  responseSchema: Record<string, unknown>;
}): Promise<T> {
  const response = await ai.models.generateContent({
    model: input.model,
    contents: `${input.system}\n\n${input.user}`,
    config: {
      responseMimeType: "application/json",
      responseSchema: input.responseSchema,
      temperature: 0.1,
    },
  });

  const text = response.text;
  if (!text) throw new Error("Gemini não retornou conteúdo estruturado");
  return JSON.parse(text) as T;
}
```

A assinatura exata de `config` deve ser conferida contra a versão instalada do pacote `@google/genai`; a REST API do Gemini usa o mesmo princípio com `generationConfig.responseMimeType = "application/json"` e `generationConfig.responseSchema` [2].

Em `server/careerAgents.ts`, o núcleo da alteração seria:

```ts
import { invokeGeminiJson } from "./_core/gemini";

const model = "gemini-3.7-flash";

// dentro de structuredJson:
const result = await invokeGeminiJson<T>({
  model,
  system,
  user,
  responseSchema: schema,
});
return result;
```

Os três agentes podem continuar com os mesmos schemas de domínio: requisitos da vaga, aderência do candidato e currículo adaptado. O prompt ético do editor deve permanecer, pois a troca de modelo não muda a regra de que o currículo não pode inventar experiências.

## 3. Onde cadastrar `GEMINI_API_KEY`

1. Criar ou visualizar a chave no [Google AI Studio](https://aistudio.google.com/apikey).
2. No Vercel, abrir o projeto e acessar **Settings → Environment Variables**.
3. Criar `GEMINI_API_KEY` sem prefixo `VITE_`.
4. Marcar **Production**, **Preview** e **Development**, conforme o ambiente desejado.
5. Fazer novo deployment, pois alterações em variáveis não afetam deployments anteriores.

A chave deve permanecer no Vercel e no gerenciador de segredos. Não deve entrar no GitHub, no `.env` commitado, em logs, em mensagens, em componentes React ou em qualquer request feito diretamente pelo navegador. O Google também recomenda restringir as chaves e acompanhar o uso para reduzir impacto de vazamento [1].

## 4. Autenticação atual

O FindWork atual usa Manus OAuth, não um OAuth genérico configurável somente por Vercel.

| Variável | Onde é usada | O que significa |
|---|---|---|
| `OAUTH_SERVER_URL` | `server/_core/env.ts`, `server/_core/sdk.ts` e `server/_core/oauth.ts` | URL base server-side usada para trocar o `code` por token e buscar os dados do usuário. Não é o portal de login. |
| `VITE_APP_ID` | `client/src/const.ts` e no payload da sessão em `server/_core/sdk.ts` | Identificador público da aplicação OAuth. O frontend envia esse ID ao portal de login. Não é uma senha. |
| `VITE_OAUTH_PORTAL_URL` | `client/src/const.ts` | URL pública do portal que inicia o login. O código monta `${portal}/app-auth`. |
| `OWNER_OPEN_ID` | `server/_core/env.ts` e `server/db.ts` | Identificador estável do usuário no provedor OAuth. Quando coincide com o usuário autenticado, o código pode promovê-lo a `admin`. Não deve ser confundido com e-mail. |

### Fluxo atual

`client/src/const.ts` monta o redirect dinamicamente com `window.location.origin` e usa `/api/oauth/callback`. `server/_core/oauth.ts` valida o `state` e o nonce do cookie, troca o código, busca `openId`, grava o usuário e cria o cookie de sessão. `server/_core/sdk.ts` encapsula a comunicação com o provedor e a assinatura/verificação do JWT local.

Ao publicar no Vercel mantendo Manus OAuth, os valores precisam continuar apontando para a mesma aplicação OAuth, e o provedor deve aceitar a URL de produção:

```text
https://SEU-PROJETO.vercel.app/api/oauth/callback
```

O código atual já usa a origem real do navegador; não substitua isso por um domínio fixo dentro do frontend. Se o provedor aceitar URLs de preview, cadastre-as separadamente ou mantenha um ambiente de preview próprio.

## 5. Se quiser trocar Manus OAuth por outro provedor

Não basta trocar quatro variáveis. Será necessário adaptar ou substituir `server/_core/sdk.ts` e `server/_core/oauth.ts` para o contrato do novo provedor: endpoint de autorização, troca de código, endpoint de user info, campos do usuário, escopos, redirect URI, logout e validação de sessão. `VITE_APP_ID` e `VITE_OAUTH_PORTAL_URL` também receberão os valores do novo provedor.

O campo `OWNER_OPEN_ID` deverá receber o valor do identificador estável retornado pelo novo provedor, geralmente o `sub` do usuário autenticado. Como esse valor não deve ser adivinhado por e-mail, o procedimento seguro é fazer um login controlado, observar o identificador no fluxo server-side sem registrar tokens e então configurá-lo no Vercel.

A proteção de `state` + nonce deve ser mantida. O callback deve falhar fechado quando o nonce não corresponder ao cookie e nunca deve trocar o `code` antes dessa validação.

## 6. Separação final de segredos

| Pode aparecer no build do frontend | Deve ficar exclusivamente no servidor |
|---|---|
| `VITE_APP_ID` | `GEMINI_API_KEY` |
| `VITE_OAUTH_PORTAL_URL` | `DATABASE_URL` |
| `VITE_ANALYTICS_ENDPOINT` | `DATABASE_URL_DIRECT` |
| `VITE_ANALYTICS_WEBSITE_ID` | `JWT_SECRET` |
| `VITE_APP_TITLE` | `OAUTH_SERVER_URL`, se o servidor precisar do endpoint privado |
| `VITE_APP_LOGO` | `OWNER_OPEN_ID` e credenciais OAuth server-side |

### Referências

[1]: https://ai.google.dev/gemini-api/docs/api-key — Google AI for Developers, “Using Gemini API keys”.
[2]: https://ai.google.dev/gemini-api/docs/generate-content/structured-output — Google AI for Developers, “Structured outputs”.
