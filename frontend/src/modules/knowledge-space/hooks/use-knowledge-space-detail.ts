"use client";

import { useQuery } from "@tanstack/react-query";

import { getKnowledgeSpace } from "../api";
import { knowledgeSpaceQueryKeys } from "./use-knowledge-space-list";

export function useKnowledgeSpaceDetail(
  knowledgeSpaceId: string | null,
) {
  return useQuery({
    queryKey: knowledgeSpaceQueryKeys.detail(
      knowledgeSpaceId ?? "",
    ),
    queryFn: () => getKnowledgeSpace(knowledgeSpaceId ?? ""),
    enabled: Boolean(knowledgeSpaceId),
  });
}
