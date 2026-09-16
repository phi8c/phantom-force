import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { ingestionApi } from "../api/ingestion.api";
import type {
  CreateIngestionRequest,
  IngestionConfigurationRequest,
  IngestionScopeRequest,
} from "../types/ingestion.types";

export const ingestionQueryKeys = {
  all: ["ingestion"] as const,
  master: () => [...ingestionQueryKeys.all, "master"] as const,
  extractionEngines: () =>
    [...ingestionQueryKeys.master(), "extraction-engines"] as const,
  chunkingStrategies: () =>
    [...ingestionQueryKeys.master(), "chunking-strategies"] as const,
  configuration: (jobId: string) =>
    [...ingestionQueryKeys.all, "configuration", jobId] as const,
  scope: (jobId: string) =>
    [...ingestionQueryKeys.all, "scope", jobId] as const,
};

export function useCreateIngestionJob() {
  return useMutation({
    mutationFn: (payload: CreateIngestionRequest) =>
      ingestionApi.createJob(payload),
  });
}

export function useExtractionEngines() {
  return useQuery({
    queryKey: ingestionQueryKeys.extractionEngines(),
    queryFn: () => ingestionApi.listExtractionEngines(),
  });
}

export function useChunkingStrategies() {
  return useQuery({
    queryKey: ingestionQueryKeys.chunkingStrategies(),
    queryFn: () => ingestionApi.listChunkingStrategies(),
  });
}

export function useIngestionConfiguration(jobId: string | null) {
  return useQuery({
    queryKey: ingestionQueryKeys.configuration(jobId ?? ""),
    queryFn: () => ingestionApi.getConfiguration(jobId ?? ""),
    enabled: Boolean(jobId),
  });
}

export function useSaveIngestionConfiguration(jobId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: IngestionConfigurationRequest) =>
      ingestionApi.saveConfiguration(jobId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ingestionQueryKeys.configuration(jobId),
      });
    },
  });
}

export function useIngestionScope(jobId: string | null) {
  return useQuery({
    queryKey: ingestionQueryKeys.scope(jobId ?? ""),
    queryFn: () => ingestionApi.getScope(jobId ?? ""),
    enabled: Boolean(jobId),
  });
}

export function useSaveIngestionScope(jobId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: IngestionScopeRequest) =>
      ingestionApi.saveScope(jobId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ingestionQueryKeys.scope(jobId),
      });
    },
  });
}

export function useStartIngestionJob() {
  return useMutation({
    mutationFn: ({
      jobId,
      batchSize,
    }: {
      jobId: string;
      batchSize?: number;
    }) => ingestionApi.startJob(jobId, batchSize),
  });
}
