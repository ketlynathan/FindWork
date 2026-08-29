export type SubmissionCandidate = {
  approvalConfirmed: boolean;
  approvedAt: Date | null;
};

export function assertExplicitApproval(application: SubmissionCandidate) {
  if (!application.approvalConfirmed || !application.approvedAt) {
    throw new Error("A candidatura exige aprovação explícita antes de qualquer registro de envio.");
  }
}

export function assertNoExcludedClaimInResume(adaptedResume: string, excludedClaims: string[]) {
  const normalizedResume = adaptedResume.toLocaleLowerCase("pt-BR");
  const conflictingClaim = excludedClaims.find(claim => {
    const normalizedClaim = claim.trim().toLocaleLowerCase("pt-BR");
    return normalizedClaim.length >= 12 && normalizedResume.includes(normalizedClaim);
  });
  if (conflictingClaim) {
    throw new Error("O currículo adaptado contém uma afirmação que o agente identificou como não comprovada pelo currículo-fonte.");
  }
}
