"use client";

import { useQuery } from "@tanstack/react-query";

import { listEmbeddingModels } from "../api";

export const embeddingModelQueryKeys = {
  all: ["embedding-models"] as const,
  list: () =>
    [...embeddingModelQueryKeys.all, "list"] as const,
};

export function useEmbeddingModels() {
  return useQuery({
    queryKey: embeddingModelQueryKeys.list(),
    queryFn: listEmbeddingModels,
  });
}
