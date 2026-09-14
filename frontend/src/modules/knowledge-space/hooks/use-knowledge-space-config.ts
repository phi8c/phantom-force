"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getKnowledgeSpaceDataHubConfig,
  getKnowledgeSpaceEmbeddingConfig,
  saveKnowledgeSpaceDataHubConfig,
  saveKnowledgeSpaceEmbeddingConfig,
} from "../api";
import type {
  SaveDataHubConfigPayload,
  SaveEmbeddingConfigPayload,
} from "../types";
import { knowledgeSpaceQueryKeys } from "./use-knowledge-space-list";

export function useKnowledgeSpaceDataHubConfig(
  knowledgeSpaceId: string | null,
) {
  return useQuery({
    queryKey: knowledgeSpaceQueryKeys.dataHubConfig(
      knowledgeSpaceId ?? "",
    ),
    queryFn: () =>
      getKnowledgeSpaceDataHubConfig(
        knowledgeSpaceId ?? "",
      ),
    enabled: Boolean(knowledgeSpaceId),
  });
}

export function useSaveKnowledgeSpaceDataHubConfig(
  knowledgeSpaceId: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SaveDataHubConfigPayload) =>
      saveKnowledgeSpaceDataHubConfig(
        knowledgeSpaceId,
        payload,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: knowledgeSpaceQueryKeys.dataHubConfig(
          knowledgeSpaceId,
        ),
      });
    },
  });
}

export function useKnowledgeSpaceEmbeddingConfig(
  knowledgeSpaceId: string | null,
) {
  return useQuery({
    queryKey: knowledgeSpaceQueryKeys.embeddingConfig(
      knowledgeSpaceId ?? "",
    ),
    queryFn: () =>
      getKnowledgeSpaceEmbeddingConfig(
        knowledgeSpaceId ?? "",
      ),
    enabled: Boolean(knowledgeSpaceId),
  });
}

export function useSaveKnowledgeSpaceEmbeddingConfig(
  knowledgeSpaceId: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SaveEmbeddingConfigPayload) =>
      saveKnowledgeSpaceEmbeddingConfig(
        knowledgeSpaceId,
        payload,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: knowledgeSpaceQueryKeys.embeddingConfig(
          knowledgeSpaceId,
        ),
      });
    },
  });
}
