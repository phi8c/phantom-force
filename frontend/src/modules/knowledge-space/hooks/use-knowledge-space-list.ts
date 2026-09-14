"use client";

import { useQuery } from "@tanstack/react-query";

import { listKnowledgeSpaces } from "../api";
import type { ListKnowledgeSpacesParams } from "../types";

export const knowledgeSpaceQueryKeys = {
  all: ["knowledge-spaces"] as const,
  list: (params: ListKnowledgeSpacesParams) =>
    [...knowledgeSpaceQueryKeys.all, "list", params] as const,
  detail: (id: string) =>
    [...knowledgeSpaceQueryKeys.all, "detail", id] as const,
  dataHubConfig: (id: string) =>
    [...knowledgeSpaceQueryKeys.detail(id), "data-hub"] as const,
  embeddingConfig: (id: string) =>
    [...knowledgeSpaceQueryKeys.detail(id), "embedding"] as const,
};

export function useKnowledgeSpaceList(
  params: ListKnowledgeSpacesParams,
) {
  return useQuery({
    queryKey: knowledgeSpaceQueryKeys.list(params),
    queryFn: () => listKnowledgeSpaces(params),
  });
}
