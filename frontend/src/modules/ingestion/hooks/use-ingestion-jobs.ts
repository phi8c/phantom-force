"use client";

import { useQuery } from "@tanstack/react-query";

import { ingestionApi } from "../api/ingestion.api";
import type { IngestionFilters } from "../types/ingestion.types";
import { ingestionQueryKeys } from "./use-ingestion-config";

export function useIngestionJobs(
  filters: IngestionFilters,
  knowledgeSpaceId?: string,
) {
  return useQuery({
    queryKey: [
      ...ingestionQueryKeys.all,
      "jobs",
      knowledgeSpaceId ?? "",
      filters.status,
    ],
    queryFn: () =>
      ingestionApi.getJobs({
        knowledgeSpaceId,
        status:
          filters.status === "ALL"
            ? undefined
            : filters.status,
        limit: 20,
      }),
  });
}
