import { invokeLLM } from "./_core/llm";
import type { MatchBreakdown, StructuredJobRequirements } from "../drizzle/schema";

const model = "gpt-5-mini";

function readContent(content: string | unknown[]): string {
  if (typeof content === "string") return content;
  return content.map(item => typeof item === "object" && item && "text" in item ? String((item as { text: unknown }).text) : "").join("\n");
}

async function structuredJson<T>(name: string, schema: Record<string, unknown>, system: string, user: string): Promise<T> {
  const response = await invokeLLM({
    model,
    messages: [{ role: "system", content: system }, { role: "user", content: user }],
    response_format: { type: "json_schema", json_schema: { name, strict: true, schema } },
  });
  const content = readContent(response.choices[0]?.message.content ?? "");
  if (!content) throw new Error("A análise não retornou conteúdo estruturado.");
  return JSON.parse(content) as T;
}

export async function analyzeJobRequirements(input: { title: string; description: string; workMode: string }) {
  const schema = {
    type: "object",
    properties: {
      seniority: { type: "string" },
      workMode: { type: "string" },
      requiredSkills: { type: "array", items: { type: "string" } },
      desiredSkills: { type: "array", items: { type: "string" } },
      responsibilities: { type: "array", items: { type: "string" } },
      keywords: { type: "array", items: { type: "string" } },
    },
    required: ["seniority", "workMode", "requiredSkills", "desiredSkills", "responsibilities", "keywords"],
    additionalProperties: false,
  };
  return structuredJson<StructuredJobRequirements>("job_requirements", schema, "Você é um analista de vagas. Extraia somente requisitos sustentados pelo texto. Não invente exigências, salário, benefícios ou senioridade. Normalize nomes de competências sem acrescentar informações inexistentes.", `Cargo: ${input.title}\nModalidade informada: ${input.workMode}\n\nDescrição da vaga:\n${input.description}`);
}

export async function evaluateFit(input: { profile: { professionalArea: string; targetRole: string; seniority: string; summary: string; skills: string[]; regions: string[]; workModes: string[] }; job: { title: string; professionalArea: string; region: string; workMode: string; structuredRequirements: StructuredJobRequirements | null; description: string } }) {
  const schema = {
    type: "object",
    properties: {
      score: { type: "integer", minimum: 0, maximum: 100 },
      priority: { type: "string", enum: ["high", "medium", "low"] },
      shouldApply: { type: "boolean" },
      strengths: { type: "array", items: { type: "string" } },
      gaps: { type: "array", items: { type: "string" } },
      rationale: { type: "string" },
      interviewFocus: { type: "array", items: { type: "string" } },
    },
    required: ["score", "priority", "shouldApply", "strengths", "gaps", "rationale", "interviewFocus"],
    additionalProperties: false,
  };
  return structuredJson<MatchBreakdown & { shouldApply: boolean }>("candidate_match", schema, "Você é um recrutador sênior imparcial. Compare o perfil e a vaga com rigor. Pontue apenas competências presentes no perfil. Trate lacunas como lacunas, sem sugerir que o candidato possui experiência que não declarou. A recomendação deve considerar área, senioridade, localização e modalidade.", `PERFIL\n${JSON.stringify(input.profile)}\n\nVAGA\n${JSON.stringify(input.job)}`);
}

export async function tailorResume(input: { resumeText: string; profile: { targetRole: string; professionalArea: string; skills: string[] }; job: { title: string; company: string; description: string; structuredRequirements: StructuredJobRequirements | null } }) {
  const schema = {
    type: "object",
    properties: {
      adaptedResume: { type: "string" },
      factsUsed: { type: "array", items: { type: "string" } },
      excludedClaims: { type: "array", items: { type: "string" } },
      verificationNote: { type: "string" },
    },
    required: ["adaptedResume", "factsUsed", "excludedClaims", "verificationNote"],
    additionalProperties: false,
  };
  return structuredJson<{ adaptedResume: string; factsUsed: string[]; excludedClaims: string[]; verificationNote: string }>("adapted_resume", schema, "Você é um editor de currículo ético. Reorganize e enfatize SOMENTE fatos, competências, projetos, resultados e experiências que existam no currículo-fonte. Nunca invente cargo, empresa, data, certificação, ferramenta, nível de domínio ou conquista. Não tente ocultar lacunas criando frases ambíguas. Retorne um currículo claro, profissional e direcionado à vaga.", `PERFIL\n${JSON.stringify(input.profile)}\n\nVAGA\n${JSON.stringify(input.job)}\n\nCURRÍCULO-FONTE\n${input.resumeText}`);
}
