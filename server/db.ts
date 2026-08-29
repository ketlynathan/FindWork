import { and, desc, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  agentActivities,
  applications,
  candidateProfiles,
  integrations,
  jobAnalyses,
  jobs,
  resumeDocuments,
  type InsertUser,
  users,
} from "../drizzle/schema";
import { ENV } from "./_core/env";
import { assertExplicitApproval } from "./careerPolicy";

let _db: ReturnType<typeof drizzle> | null = null;

export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

async function requireDb() {
  const db = await getDb();
  if (!db) throw new Error("O banco de dados não está disponível no momento.");
  return db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) throw new Error("User openId is required for upsert");
  const db = await requireDb();
  const values: InsertUser = { openId: user.openId };
  const updateSet: Record<string, unknown> = {};
  (["name", "email", "loginMethod"] as const).forEach(field => {
    if (user[field] !== undefined) {
      values[field] = user[field] ?? null;
      updateSet[field] = user[field] ?? null;
    }
  });
  values.lastSignedIn = user.lastSignedIn ?? new Date();
  updateSet.lastSignedIn = values.lastSignedIn;
  if (user.role !== undefined) {
    values.role = user.role;
    updateSet.role = user.role;
  } else if (user.openId === ENV.ownerOpenId) {
    values.role = "admin";
    updateSet.role = "admin";
  }
  await db.insert(users).values(values).onDuplicateKeyUpdate({ set: updateSet });
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);
  return result[0];
}

export async function getProfiles(userId: number) {
  const db = await requireDb();
  return db.select().from(candidateProfiles).where(eq(candidateProfiles.userId, userId)).orderBy(desc(candidateProfiles.updatedAt));
}

export async function getProfile(userId: number, profileId: number) {
  const db = await requireDb();
  const result = await db.select().from(candidateProfiles).where(and(eq(candidateProfiles.id, profileId), eq(candidateProfiles.userId, userId))).limit(1);
  return result[0];
}

export async function saveProfile(userId: number, input: Omit<typeof candidateProfiles.$inferInsert, "userId" | "id" | "createdAt" | "updatedAt"> & { id?: number }) {
  const db = await requireDb();
  const { id, ...values } = input;
  if (id) {
    const owned = await getProfile(userId, id);
    if (!owned) throw new Error("Perfil não encontrado.");
    await db.update(candidateProfiles).set({ ...values, updatedAt: new Date() }).where(and(eq(candidateProfiles.id, id), eq(candidateProfiles.userId, userId)));
    return getProfile(userId, id);
  }
  const ids = await db.insert(candidateProfiles).values({ ...values, userId }).$returningId();
  return getProfile(userId, Number(ids[0]?.id));
}

export async function saveResumeDocument(userId: number, input: Omit<typeof resumeDocuments.$inferInsert, "userId" | "id" | "createdAt" | "isActive">) {
  const db = await requireDb();
  const profile = await getProfile(userId, input.profileId);
  if (!profile) throw new Error("O perfil não pertence à sua conta.");
  await db.update(resumeDocuments).set({ isActive: false }).where(and(eq(resumeDocuments.userId, userId), eq(resumeDocuments.profileId, input.profileId)));
  const ids = await db.insert(resumeDocuments).values({ ...input, userId, isActive: true }).$returningId();
  return Number(ids[0]?.id);
}

export async function createJob(userId: number, input: Omit<typeof jobs.$inferInsert, "userId" | "id" | "createdAt" | "updatedAt" | "structuredRequirements">) {
  const db = await requireDb();
  const existing = await db.select().from(jobs).where(and(eq(jobs.userId, userId), eq(jobs.sourceUrl, input.sourceUrl))).limit(1);
  if (existing[0]) throw new Error("Esta vaga já foi adicionada à sua base consolidada.");
  const ids = await db.insert(jobs).values({ ...input, userId, structuredRequirements: null }).$returningId();
  return getJob(userId, Number(ids[0]?.id));
}

export async function getJob(userId: number, jobId: number) {
  const db = await requireDb();
  const result = await db.select().from(jobs).where(and(eq(jobs.id, jobId), eq(jobs.userId, userId))).limit(1);
  return result[0];
}

export async function listJobs(userId: number, filters: { query?: string; region?: string; area?: string; workMode?: "remote" | "hybrid" | "onsite" | "flexible"; profileId?: number }) {
  const db = await requireDb();
  const allJobs = await db.select().from(jobs).where(eq(jobs.userId, userId)).orderBy(desc(jobs.createdAt));
  const normalized = (value?: string) => value?.trim().toLocaleLowerCase("pt-BR") ?? "";
  const query = normalized(filters.query);
  const region = normalized(filters.region);
  const area = normalized(filters.area);
  const filtered = allJobs.filter(job => {
    const haystack = `${job.title} ${job.company} ${job.location} ${job.region} ${job.professionalArea} ${job.description}`.toLocaleLowerCase("pt-BR");
    return (!query || haystack.includes(query)) && (!region || job.region.toLocaleLowerCase("pt-BR").includes(region)) && (!area || job.professionalArea.toLocaleLowerCase("pt-BR").includes(area)) && (!filters.workMode || job.workMode === filters.workMode);
  });
  if (!filters.profileId) return filtered.map(job => ({ job, analysis: null }));
  const profile = await getProfile(userId, filters.profileId);
  if (!profile) throw new Error("Perfil não encontrado.");
  const analyses = await db.select().from(jobAnalyses).where(and(eq(jobAnalyses.userId, userId), eq(jobAnalyses.profileId, filters.profileId)));
  const byJobId = new Map(analyses.map(analysis => [analysis.jobId, analysis]));
  return filtered.map(job => ({ job, analysis: byJobId.get(job.id) ?? null }));
}

export async function saveStructuredRequirements(userId: number, jobId: number, structuredRequirements: NonNullable<typeof jobs.$inferInsert["structuredRequirements"]>) {
  const db = await requireDb();
  const job = await getJob(userId, jobId);
  if (!job) throw new Error("Vaga não encontrada.");
  await db.update(jobs).set({ structuredRequirements, updatedAt: new Date() }).where(and(eq(jobs.id, jobId), eq(jobs.userId, userId)));
  return getJob(userId, jobId);
}

export async function saveAnalysis(userId: number, profileId: number, jobId: number, input: Omit<typeof jobAnalyses.$inferInsert, "userId" | "profileId" | "jobId" | "id" | "createdAt" | "updatedAt">) {
  const db = await requireDb();
  const existing = await db.select().from(jobAnalyses).where(and(eq(jobAnalyses.userId, userId), eq(jobAnalyses.profileId, profileId), eq(jobAnalyses.jobId, jobId))).limit(1);
  if (existing[0]) {
    await db.update(jobAnalyses).set({ ...input, updatedAt: new Date() }).where(eq(jobAnalyses.id, existing[0].id));
    return existing[0].id;
  }
  const ids = await db.insert(jobAnalyses).values({ ...input, userId, profileId, jobId }).$returningId();
  return Number(ids[0]?.id);
}

export async function logAgentActivity(userId: number, input: Omit<typeof agentActivities.$inferInsert, "userId" | "id" | "createdAt">) {
  const db = await requireDb();
  await db.insert(agentActivities).values({ ...input, userId });
}

export async function getRecentActivities(userId: number) {
  const db = await requireDb();
  return db.select().from(agentActivities).where(eq(agentActivities.userId, userId)).orderBy(desc(agentActivities.createdAt)).limit(12);
}

export async function createApplicationDraft(userId: number, input: { profileId: number; jobId: number; adaptedResume: string; adaptationNote: string }) {
  const db = await requireDb();
  const profile = await getProfile(userId, input.profileId);
  const job = await getJob(userId, input.jobId);
  if (!profile || !job) throw new Error("O perfil ou a vaga não pertencem à sua conta.");
  const existing = await db.select().from(applications).where(and(eq(applications.userId, userId), eq(applications.profileId, input.profileId), eq(applications.jobId, input.jobId))).limit(1);
  const initialLog = [{ at: new Date().toISOString(), action: "Rascunho gerado", note: "Currículo adaptado aguardando revisão e aprovação explícita." }];
  if (existing[0]) {
    await db.update(applications).set({ adaptedResume: input.adaptedResume, adaptationNote: input.adaptationNote, status: "draft", approvalConfirmed: false, approvedAt: null, submittedAt: null, activityLog: initialLog, updatedAt: new Date() }).where(eq(applications.id, existing[0].id));
    return existing[0].id;
  }
  const ids = await db.insert(applications).values({ userId, profileId: input.profileId, jobId: input.jobId, adaptedResume: input.adaptedResume, adaptationNote: input.adaptationNote, applicationUrl: job.sourceUrl, activityLog: initialLog }).$returningId();
  return Number(ids[0]?.id);
}

export async function listApplications(userId: number) {
  const db = await requireDb();
  return db.select({ application: applications, profile: candidateProfiles, job: jobs }).from(applications).innerJoin(candidateProfiles, eq(applications.profileId, candidateProfiles.id)).innerJoin(jobs, eq(applications.jobId, jobs.id)).where(eq(applications.userId, userId)).orderBy(desc(applications.updatedAt));
}

export async function approveApplication(userId: number, applicationId: number) {
  const db = await requireDb();
  const current = await db.select().from(applications).where(and(eq(applications.id, applicationId), eq(applications.userId, userId))).limit(1);
  if (!current[0]) throw new Error("Rascunho de candidatura não encontrado.");
  if (!current[0].adaptedResume.trim()) throw new Error("Um currículo adaptado precisa ser revisado antes da aprovação.");
  const approvedAt = new Date();
  const log = [...current[0].activityLog, { at: approvedAt.toISOString(), action: "Candidatura aprovada", note: "Aprovação explícita registrada pelo usuário." }];
  await db.update(applications).set({ status: "approved", approvalConfirmed: true, approvedAt, activityLog: log, updatedAt: approvedAt }).where(and(eq(applications.id, applicationId), eq(applications.userId, userId)));
}

export async function recordApplicationSubmission(userId: number, applicationId: number) {
  const db = await requireDb();
  const current = await db.select().from(applications).where(and(eq(applications.id, applicationId), eq(applications.userId, userId))).limit(1);
  if (!current[0]) throw new Error("Candidatura não encontrada.");
  assertExplicitApproval(current[0]);
  const submittedAt = new Date();
  const log = [...current[0].activityLog, { at: submittedAt.toISOString(), action: "Envio registrado", note: "O usuário confirmou que concluiu a candidatura na plataforma oficial." }];
  await db.update(applications).set({ status: "submitted", submittedAt, activityLog: log, updatedAt: submittedAt }).where(and(eq(applications.id, applicationId), eq(applications.userId, userId)));
}

export async function getIntegrations(userId: number) {
  const db = await requireDb();
  return db.select().from(integrations).where(eq(integrations.userId, userId)).orderBy(desc(integrations.updatedAt));
}

export async function saveIntegration(userId: number, input: Omit<typeof integrations.$inferInsert, "userId" | "id" | "createdAt" | "updatedAt" | "secretReference">) {
  const db = await requireDb();
  const existing = await db.select().from(integrations).where(and(eq(integrations.userId, userId), eq(integrations.provider, input.provider), eq(integrations.accountLabel, input.accountLabel))).limit(1);
  if (existing[0]) {
    await db.update(integrations).set({ ...input, secretReference: null, updatedAt: new Date() }).where(eq(integrations.id, existing[0].id));
    return existing[0].id;
  }
  const ids = await db.insert(integrations).values({ ...input, userId, secretReference: null }).$returningId();
  return Number(ids[0]?.id);
}

export async function getDashboard(userId: number) {
  const db = await requireDb();
  const [profiles, jobsCount, analyses, applicationsList, activities] = await Promise.all([
    getProfiles(userId),
    db.select().from(jobs).where(eq(jobs.userId, userId)),
    db.select().from(jobAnalyses).where(eq(jobAnalyses.userId, userId)),
    db.select().from(applications).where(eq(applications.userId, userId)),
    getRecentActivities(userId),
  ]);
  const recommended = analyses.filter(item => item.shouldApply).length;
  const approved = applicationsList.filter(item => item.status === "approved").length;
  const submitted = applicationsList.filter(item => item.status === "submitted").length;
  const averageScore = analyses.length ? Math.round(analyses.reduce((sum, item) => sum + item.matchScore, 0) / analyses.length) : 0;
  return { profiles, activities, metrics: { jobs: jobsCount.length, recommended, approved, submitted, averageScore } };
}
