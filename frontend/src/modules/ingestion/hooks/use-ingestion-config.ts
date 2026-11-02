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

export function useExtractionEngines(enabled = true) {
  return useQuery({
    queryKey: ingestionQueryKeys.extractionEngines(),
    queryFn: () => ingestionApi.listExtractionEngines(),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useChunkingStrategies(enabled = true) {
  return useQuery({
    queryKey: ingestionQueryKeys.chunkingStrategies(),
    queryFn: () => ingestionApi.listChunkingStrategies(),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useIngestionConfiguration(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ingestionQueryKeys.configuration(jobId ?? ""),
    queryFn: () => ingestionApi.getConfiguration(jobId ?? ""),
    enabled: enabled && Boolean(jobId),
    refetchOnWindowFocus: false,
  });
}

export function useSaveIngestionConfiguration(jobId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: IngestionConfigurationRequest) =>
      ingestionApi.saveConfiguration(jobId, payload),
    onMutate: () => queryClient.cancelQueries({
      queryKey: ingestionQueryKeys.configuration(jobId),
    }),
    onSuccess: (data) => {
      queryClient.setQueryData(ingestionQueryKeys.configuration(jobId), {
        configured: true,
        data,
      });
    },
  });
}

export function useIngestionScope(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ingestionQueryKeys.scope(jobId ?? ""),
    queryFn: () => ingestionApi.getScope(jobId ?? ""),
    enabled: enabled && Boolean(jobId),
    refetchOnWindowFocus: false,
  });
}

export function useSaveIngestionScope(jobId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: IngestionScopeRequest) =>
      ingestionApi.saveScope(jobId, payload),
    onMutate: () => queryClient.cancelQueries({
      queryKey: ingestionQueryKeys.scope(jobId),
    }),
    onSuccess: (data) => {
      queryClient.setQueryData(ingestionQueryKeys.scope(jobId), {
        configured: true,
        data,
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
