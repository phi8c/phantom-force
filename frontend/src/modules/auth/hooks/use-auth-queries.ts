"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getCurrentUser,
  getKnowledgeSpaceAuthRequirement,
} from "../api";
import { authQueryKeys } from "./auth-query-keys";

export function useCurrentUser() {
  return useQuery({
    queryKey: authQueryKeys.currentUser(),
    queryFn: getCurrentUser,
    retry: false,
  });
}

export function useKnowledgeSpaceAuthRequirement(
  knowledgeSpaceId: string | null,
) {
  return useQuery({
    queryKey: authQueryKeys.knowledgeSpaceRequirement(
      knowledgeSpaceId ?? "",
    ),
    queryFn: () =>
      getKnowledgeSpaceAuthRequirement(knowledgeSpaceId ?? ""),
    enabled: Boolean(knowledgeSpaceId),
    retry: false,
  });
}
