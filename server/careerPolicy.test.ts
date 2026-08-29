import { describe, expect, it } from "vitest";
import { assertExplicitApproval, assertNoExcludedClaimInResume } from "./careerPolicy";

describe("políticas críticas de candidatura", () => {
  it("bloqueia o envio antes da aprovação explícita", () => {
    expect(() => assertExplicitApproval({ approvalConfirmed: false, approvedAt: null })).toThrow("aprovação explícita");
  });

  it("permite o registro de envio depois da aprovação explícita", () => {
    expect(() => assertExplicitApproval({ approvalConfirmed: true, approvedAt: new Date() })).not.toThrow();
  });

  it("bloqueia um currículo adaptado se ele repetir uma afirmação excluída", () => {
    expect(() => assertNoExcludedClaimInResume("Profissional com certificação Kubernetes avançada.", ["certificação Kubernetes avançada"])).toThrow("não comprovada");
  });
});
