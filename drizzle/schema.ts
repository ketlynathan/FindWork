import {
  boolean,
  int,
  json,
  mysqlEnum,
  mysqlTable,
  text,
  timestamp,
  uniqueIndex,
  varchar,
} from "drizzle-orm/mysql-core";

export type StructuredJobRequirements = {
  seniority: string;
  workMode: string;
  requiredSkills: string[];
  desiredSkills: string[];
  responsibilities: string[];
  keywords: string[];
};

export type MatchBreakdown = {
  score: number;
  priority: "high" | "medium" | "low";
  strengths: string[];
  gaps: string[];
  rationale: string;
  interviewFocus: string[];
};

export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export const candidateProfiles = mysqlTable("candidateProfiles", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  label: varchar("label", { length: 120 }).notNull(),
  professionalArea: varchar("professionalArea", { length: 160 }).notNull(),
  targetRole: varchar("targetRole", { length: 180 }).notNull(),
  seniority: varchar("seniority", { length: 80 }).notNull(),
  summary: text("summary").notNull(),
  skills: json("skills").$type<string[]>().notNull(),
  regions: json("regions").$type<string[]>().notNull(),
  workModes: json("workModes").$type<string[]>().notNull(),
  resumeText: text("resumeText").notNull(),
  isPrimary: boolean("isPrimary").default(false).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, table => [uniqueIndex("candidate_profile_owner_label_idx").on(table.userId, table.label)]);

export const resumeDocuments = mysqlTable("resumeDocuments", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  profileId: int("profileId").notNull().references(() => candidateProfiles.id, { onDelete: "cascade" }),
  fileName: varchar("fileName", { length: 255 }).notNull(),
  mimeType: varchar("mimeType", { length: 120 }).notNull(),
  storageKey: varchar("storageKey", { length: 512 }).notNull(),
  storageUrl: varchar("storageUrl", { length: 1024 }).notNull(),
  sizeBytes: int("sizeBytes").notNull(),
  isActive: boolean("isActive").default(true).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export const jobs = mysqlTable("jobs", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  title: varchar("title", { length: 220 }).notNull(),
  company: varchar("company", { length: 220 }).notNull(),
  location: varchar("location", { length: 220 }).notNull(),
  region: varchar("region", { length: 160 }).notNull(),
  professionalArea: varchar("professionalArea", { length: 160 }).notNull(),
  workMode: mysqlEnum("workMode", ["remote", "hybrid", "onsite", "flexible"]).notNull(),
  source: varchar("source", { length: 120 }).notNull(),
  sourceUrl: varchar("sourceUrl", { length: 2048 }).notNull(),
  description: text("description").notNull(),
  structuredRequirements: json("structuredRequirements").$type<StructuredJobRequirements | null>(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, table => [uniqueIndex("job_owner_url_idx").on(table.userId, table.sourceUrl)]);

export const jobAnalyses = mysqlTable("jobAnalyses", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  profileId: int("profileId").notNull().references(() => candidateProfiles.id, { onDelete: "cascade" }),
  jobId: int("jobId").notNull().references(() => jobs.id, { onDelete: "cascade" }),
  matchScore: int("matchScore").notNull(),
  priority: mysqlEnum("priority", ["high", "medium", "low"]).notNull(),
  shouldApply: boolean("shouldApply").notNull(),
  breakdown: json("breakdown").$type<MatchBreakdown>().notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, table => [uniqueIndex("job_analysis_profile_job_idx").on(table.userId, table.profileId, table.jobId)]);

export const applications = mysqlTable("applications", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  profileId: int("profileId").notNull().references(() => candidateProfiles.id, { onDelete: "cascade" }),
  jobId: int("jobId").notNull().references(() => jobs.id, { onDelete: "cascade" }),
  status: mysqlEnum("status", ["draft", "approved", "submitted", "rejected", "archived"]).default("draft").notNull(),
  adaptedResume: text("adaptedResume").notNull(),
  adaptationNote: text("adaptationNote").notNull(),
  approvalConfirmed: boolean("approvalConfirmed").default(false).notNull(),
  approvedAt: timestamp("approvedAt"),
  submittedAt: timestamp("submittedAt"),
  applicationUrl: varchar("applicationUrl", { length: 2048 }).notNull(),
  activityLog: json("activityLog").$type<Array<{ at: string; action: string; note: string }>>().notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, table => [uniqueIndex("application_profile_job_idx").on(table.userId, table.profileId, table.jobId)]);

export const integrations = mysqlTable("integrations", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  provider: varchar("provider", { length: 120 }).notNull(),
  accountLabel: varchar("accountLabel", { length: 180 }).notNull(),
  connectionMethod: mysqlEnum("connectionMethod", ["official_oauth", "authorized_api", "assisted_link"]).notNull(),
  status: mysqlEnum("status", ["not_connected", "pending", "connected", "attention_required"]).default("not_connected").notNull(),
  capabilities: json("capabilities").$type<string[]>().notNull(),
  secretReference: varchar("secretReference", { length: 180 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, table => [uniqueIndex("integration_owner_provider_account_idx").on(table.userId, table.provider, table.accountLabel)]);

export const agentActivities = mysqlTable("agentActivities", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  profileId: int("profileId").references(() => candidateProfiles.id, { onDelete: "set null" }),
  agent: mysqlEnum("agent", ["analyst", "recruiter", "career_editor", "integration_guard"]).notNull(),
  title: varchar("title", { length: 240 }).notNull(),
  detail: text("detail").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;
