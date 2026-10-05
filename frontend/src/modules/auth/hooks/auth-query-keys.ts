export const authQueryKeys = {
  all: ["auth"] as const,
  currentUser: () => [...authQueryKeys.all, "me"] as const,
  knowledgeSpaceRequirements: () =>
    [...authQueryKeys.all, "knowledge-space-requirements"] as const,
  knowledgeSpaceRequirement: (knowledgeSpaceId: string) =>
    [
      ...authQueryKeys.knowledgeSpaceRequirements(),
      knowledgeSpaceId,
    ] as const,
};
