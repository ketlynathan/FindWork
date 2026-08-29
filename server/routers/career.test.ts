import { describe, expect, it, vi } from "vitest";

const dbMocks = vi.hoisted(() => ({
  approveApplication: vi.fn(),
  createApplicationDraft: vi.fn(),
  createJob: vi.fn(),
  getDashboard: vi.fn(),
  getIntegrations: vi.fn(),
  getJob: vi.fn(),
  getProfile: vi.fn(),
  getProfiles: vi.fn(),
  listApplications: vi.fn(),
  listJobs: vi.fn(),
  logAgentActivity: vi.fn(),
  recordApplicationSubmission: vi.fn(),
  saveAnalysis: vi.fn(),
  saveIntegration: vi.fn(),
  saveProfile: vi.fn(),
  saveResumeDocument: vi.fn(),
  saveStructuredRequirements: vi.fn(),
}));

vi.mock("../db", () => dbMocks);
const storageMocks = vi.hoisted(() => ({ storagePut: vi.fn() }));
vi.mock("../storage", () => storageMocks);

import { careerRouter } from "./career";

function createCaller(userId: number) {
  return careerRouter.createCaller({
    user: { id: userId, openId: `user-${userId}`, email: null, name: "Pessoa de teste", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: {} as any,
    res: {} as any,
  });
}

describe("isolamento por usuário nas procedures de carreira", () => {
  it("encaminha leituras de perfis, vagas e integrações ao usuário autenticado", async () => {
    dbMocks.getProfiles.mockResolvedValue([]);
    dbMocks.listJobs.mockResolvedValue([]);
    dbMocks.getIntegrations.mockResolvedValue([]);
    const caller = createCaller(101);

    await caller.profiles.list();
    await caller.jobs.list({});
    await caller.integrations.list();

    expect(dbMocks.getProfiles).toHaveBeenCalledWith(101);
    expect(dbMocks.listJobs).toHaveBeenCalledWith(101, {});
    expect(dbMocks.getIntegrations).toHaveBeenCalledWith(101);
  });

  it("envia a aprovação de candidatura no escopo do usuário autenticado", async () => {
    dbMocks.approveApplication.mockResolvedValue(undefined);
    dbMocks.logAgentActivity.mockResolvedValue(undefined);
    const caller = createCaller(202);

    await caller.applications.approve({ applicationId: 44, confirmed: true });

    expect(dbMocks.approveApplication).toHaveBeenCalledWith(202, 44);
    expect(dbMocks.logAgentActivity).toHaveBeenCalledWith(202, expect.objectContaining({ agent: "integration_guard" }));
  });

  it("recusa IDs de outro usuário antes de analisar ou armazenar dados sensíveis", async () => {
    dbMocks.getJob.mockResolvedValue({ id: 88, title: "Vaga privada", professionalArea: "Tecnologia", region: "Brasil", workMode: "remote", description: "Descrição suficiente para representar uma oportunidade privada." });
    dbMocks.getProfile.mockResolvedValue(undefined);
    const caller = createCaller(303);

    await expect(caller.jobs.match({ jobId: 88, profileId: 99 })).rejects.toMatchObject({ code: "NOT_FOUND" });
    await expect(caller.profiles.uploadResume({ profileId: 99, fileName: "curriculo.txt", mimeType: "text/plain", contentBase64: "Y3VycmljdWxv" })).rejects.toMatchObject({ code: "NOT_FOUND" });

    expect(dbMocks.saveAnalysis).not.toHaveBeenCalled();
    expect(storageMocks.storagePut).not.toHaveBeenCalled();
  });

  it("encaminha mutações de perfil, vaga e integração ao usuário autenticado", async () => {
    dbMocks.saveProfile.mockResolvedValue({ id: 17 });
    dbMocks.createJob.mockResolvedValue({ id: 31 });
    dbMocks.saveIntegration.mockResolvedValue(4);
    dbMocks.logAgentActivity.mockResolvedValue(undefined);
    const caller = createCaller(404);

    await caller.profiles.save({ label: "Tecnologia", professionalArea: "Tecnologia", targetRole: "Tech Lead", seniority: "Sênior", summary: "Profissional com experiência comprovada em liderança técnica, produto e entregas de software.", skills: ["Liderança"], regions: ["Brasil"], workModes: ["Remoto"], resumeText: "Currículo-fonte com histórico profissional validado e informações suficientes para análise ética.", isPrimary: true });
    await caller.jobs.add({ title: "Tech Lead", company: "Empresa", location: "São Paulo", region: "Brasil", professionalArea: "Tecnologia", workMode: "remote", source: "Fonte oficial", sourceUrl: "https://example.com/vaga-tech-lead", description: "Descrição extensa o suficiente para descrever responsabilidades, requisitos e contexto da oportunidade profissional." });
    await caller.integrations.save({ provider: "Fonte oficial", accountLabel: "Conta de teste", connectionMethod: "assisted_link", status: "pending", capabilities: ["Abertura de link"] });

    expect(dbMocks.saveProfile).toHaveBeenCalledWith(404, expect.objectContaining({ label: "Tecnologia" }));
    expect(dbMocks.createJob).toHaveBeenCalledWith(404, expect.objectContaining({ title: "Tech Lead" }));
    expect(dbMocks.saveIntegration).toHaveBeenCalledWith(404, expect.objectContaining({ provider: "Fonte oficial" }));
  });
});
