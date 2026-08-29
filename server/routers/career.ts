import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { router, protectedProcedure } from "../_core/trpc";
import { analyzeJobRequirements, evaluateFit, tailorResume } from "../careerAgents";
import { assertNoExcludedClaimInResume } from "../careerPolicy";
import { storagePut } from "../storage";
import {
  approveApplication,
  createApplicationDraft,
  createJob,
  getDashboard,
  getIntegrations,
  getJob,
  getProfile,
  getProfiles,
  listApplications,
  listJobs,
  logAgentActivity,
  recordApplicationSubmission,
  saveAnalysis,
  saveIntegration,
  saveProfile,
  saveResumeDocument,
  saveStructuredRequirements,
} from "../db";

const stringList = z.array(z.string().trim().min(1).max(100)).max(50);
const profileInput = z.object({
  id: z.number().int().positive().optional(),
  label: z.string().trim().min(2).max(120),
  professionalArea: z.string().trim().min(2).max(160),
  targetRole: z.string().trim().min(2).max(180),
  seniority: z.string().trim().min(2).max(80),
  summary: z.string().trim().min(20).max(6000),
  skills: stringList,
  regions: stringList,
  workModes: stringList,
  resumeText: z.string().trim().min(80).max(30000),
  isPrimary: z.boolean().default(false),
});
const jobInput = z.object({
  title: z.string().trim().min(2).max(220),
  company: z.string().trim().min(2).max(220),
  location: z.string().trim().min(2).max(220),
  region: z.string().trim().min(2).max(160),
  professionalArea: z.string().trim().min(2).max(160),
  workMode: z.enum(["remote", "hybrid", "onsite", "flexible"]),
  source: z.string().trim().min(2).max(120),
  sourceUrl: z.string().trim().url().max(2048),
  description: z.string().trim().min(80).max(30000),
});

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Não foi possível concluir esta operação.";
}

export const careerRouter = router({
  dashboard: protectedProcedure.query(({ ctx }) => getDashboard(ctx.user.id)),
  profiles: router({
    list: protectedProcedure.query(({ ctx }) => getProfiles(ctx.user.id)),
    save: protectedProcedure.input(profileInput).mutation(async ({ ctx, input }) => {
      const profile = await saveProfile(ctx.user.id, input);
      await logAgentActivity(ctx.user.id, { profileId: profile?.id ?? null, agent: "career_editor", title: "Perfil profissional atualizado", detail: `O perfil “${input.label}” foi salvo com currículo e preferências isolados.` });
      return profile;
    }),
    uploadResume: protectedProcedure.input(z.object({ profileId: z.number().int().positive(), fileName: z.string().trim().min(1).max(255), mimeType: z.enum(["text/plain", "text/markdown"]), contentBase64: z.string().min(1).max(4_500_000) })).mutation(async ({ ctx, input }) => {
      const profile = await getProfile(ctx.user.id, input.profileId);
      if (!profile) throw new TRPCError({ code: "NOT_FOUND", message: "Perfil não encontrado." });
      const content = Buffer.from(input.contentBase64, "base64");
      if (content.byteLength === 0 || content.byteLength > 3_000_000) throw new TRPCError({ code: "BAD_REQUEST", message: "O arquivo de currículo deve ter até 3 MB." });
      const safeName = input.fileName.replace(/[^a-zA-Z0-9._-]/g, "_");
      const stored = await storagePut(`${ctx.user.id}/resumes/${input.profileId}/${safeName}`, content, input.mimeType);
      await saveResumeDocument(ctx.user.id, { profileId: input.profileId, fileName: input.fileName, mimeType: input.mimeType, storageKey: stored.key, storageUrl: stored.url, sizeBytes: content.byteLength });
      await logAgentActivity(ctx.user.id, { profileId: input.profileId, agent: "career_editor", title: "Documento-fonte protegido", detail: `Uma nova versão do currículo “${input.fileName}” foi armazenada com segurança para este perfil.` });
      return { url: stored.url };
    }),
  }),
  jobs: router({
    list: protectedProcedure.input(z.object({ query: z.string().optional(), region: z.string().optional(), area: z.string().optional(), workMode: z.enum(["remote", "hybrid", "onsite", "flexible"]).optional(), profileId: z.number().int().positive().optional() }).optional()).query(({ ctx, input }) => listJobs(ctx.user.id, input ?? {})),
    add: protectedProcedure.input(jobInput).mutation(async ({ ctx, input }) => {
      const job = await createJob(ctx.user.id, input);
      await logAgentActivity(ctx.user.id, { profileId: null, agent: "analyst", title: "Vaga consolidada", detail: `A oportunidade “${input.title}” foi adicionada à base privada do usuário.` });
      return job;
    }),
    analyze: protectedProcedure.input(z.object({ jobId: z.number().int().positive() })).mutation(async ({ ctx, input }) => {
      const job = await getJob(ctx.user.id, input.jobId);
      if (!job) throw new TRPCError({ code: "NOT_FOUND", message: "Vaga não encontrada." });
      try {
        const requirements = await analyzeJobRequirements(job);
        await saveStructuredRequirements(ctx.user.id, job.id, requirements);
        await logAgentActivity(ctx.user.id, { profileId: null, agent: "analyst", title: "Requisitos estruturados", detail: `O agente analista estruturou os requisitos da vaga “${job.title}”.` });
        return requirements;
      } catch (error) {
        throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: errorMessage(error) });
      }
    }),
    match: protectedProcedure.input(z.object({ jobId: z.number().int().positive(), profileId: z.number().int().positive() })).mutation(async ({ ctx, input }) => {
      const [job, profile] = await Promise.all([getJob(ctx.user.id, input.jobId), getProfile(ctx.user.id, input.profileId)]);
      if (!job || !profile) throw new TRPCError({ code: "NOT_FOUND", message: "Vaga ou perfil não encontrado." });
      try {
        const result = await evaluateFit({ profile, job });
        await saveAnalysis(ctx.user.id, profile.id, job.id, { matchScore: result.score, priority: result.priority, shouldApply: result.shouldApply, breakdown: result });
        await logAgentActivity(ctx.user.id, { profileId: profile.id, agent: "recruiter", title: "Aderência calculada", detail: `O agente recrutador avaliou “${job.title}” para o perfil “${profile.label}” com ${result.score}% de aderência.` });
        return result;
      } catch (error) {
        throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: errorMessage(error) });
      }
    }),
    adaptAndDraft: protectedProcedure.input(z.object({ jobId: z.number().int().positive(), profileId: z.number().int().positive() })).mutation(async ({ ctx, input }) => {
      const [job, profile] = await Promise.all([getJob(ctx.user.id, input.jobId), getProfile(ctx.user.id, input.profileId)]);
      if (!job || !profile) throw new TRPCError({ code: "NOT_FOUND", message: "Vaga ou perfil não encontrado." });
      try {
        const result = await tailorResume({ resumeText: profile.resumeText, profile, job });
        assertNoExcludedClaimInResume(result.adaptedResume, result.excludedClaims);
        const adaptationNote = `${result.verificationNote}\n\nFatos utilizados:\n${result.factsUsed.map(item => `- ${item}`).join("\n")}\n\nAfirmações excluídas por não constarem no currículo-fonte:\n${result.excludedClaims.map(item => `- ${item}`).join("\n")}`;
        const applicationId = await createApplicationDraft(ctx.user.id, { profileId: profile.id, jobId: job.id, adaptedResume: result.adaptedResume, adaptationNote });
        await logAgentActivity(ctx.user.id, { profileId: profile.id, agent: "career_editor", title: "Rascunho de candidatura criado", detail: `O currículo para “${job.title}” foi adaptado sem criar experiências e aguarda aprovação explícita.` });
        return { applicationId, ...result };
      } catch (error) {
        throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: errorMessage(error) });
      }
    }),
  }),
  applications: router({
    list: protectedProcedure.query(({ ctx }) => listApplications(ctx.user.id)),
    approve: protectedProcedure.input(z.object({ applicationId: z.number().int().positive(), confirmed: z.literal(true) })).mutation(async ({ ctx, input }) => {
      await approveApplication(ctx.user.id, input.applicationId);
      await logAgentActivity(ctx.user.id, { profileId: null, agent: "integration_guard", title: "Aprovação explícita registrada", detail: "Uma candidatura foi liberada pelo usuário após revisão do currículo adaptado." });
      return { ok: true };
    }),
    recordSubmission: protectedProcedure.input(z.object({ applicationId: z.number().int().positive() })).mutation(async ({ ctx, input }) => {
      await recordApplicationSubmission(ctx.user.id, input.applicationId);
      return { ok: true };
    }),
  }),
  integrations: router({
    list: protectedProcedure.query(({ ctx }) => getIntegrations(ctx.user.id)),
    save: protectedProcedure.input(z.object({ provider: z.string().trim().min(2).max(120), accountLabel: z.string().trim().min(2).max(180), connectionMethod: z.enum(["official_oauth", "authorized_api", "assisted_link"]), status: z.enum(["not_connected", "pending", "connected", "attention_required"]), capabilities: stringList })).mutation(async ({ ctx, input }) => {
      const id = await saveIntegration(ctx.user.id, input);
      await logAgentActivity(ctx.user.id, { profileId: null, agent: "integration_guard", title: "Integração registrada", detail: `A integração “${input.provider}” foi registrada sem salvar ou exibir senhas.` });
      return { id };
    }),
  }),
});
