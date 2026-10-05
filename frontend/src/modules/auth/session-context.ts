import type { CurrentUser } from "./types";

export function isManagementSession(
  session: CurrentUser | undefined,
): boolean {
  return session?.context_type === "MANAGEMENT";
}

export function isKnowledgeSpaceSession(
  session: CurrentUser | undefined,
  knowledgeSpaceId: string,
): boolean {
  return (
    session?.context_type === "KNOWLEDGE_SPACE" &&
    session.knowledge_space_id === knowledgeSpaceId
  );
}

export function getSessionHomePath(session: CurrentUser): string {
  if (
    session.context_type === "KNOWLEDGE_SPACE" &&
    session.knowledge_space_id
  ) {
    return `/chat/${encodeURIComponent(session.knowledge_space_id)}`;
  }

  return "/admin";
}
