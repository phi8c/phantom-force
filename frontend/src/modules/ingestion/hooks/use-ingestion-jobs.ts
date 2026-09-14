"use client";

import { useMemo } from "react";

import { mockIngestionJobs } from "../mocks/ingestion.mock";
import type {
  IngestionFilters,
  IngestionJob,
} from "../types/ingestion.types";

export function useIngestionJobs(
  filters: IngestionFilters,
): IngestionJob[] {
  return useMemo(() => {
    const search = filters.search.trim().toLowerCase();

    return mockIngestionJobs.filter((job) => {
      const matchesSearch =
        !search ||
        job.name.toLowerCase().includes(search) ||
        job.sourceName.toLowerCase().includes(search) ||
        job.knowledgeSpaceName.toLowerCase().includes(search);

      const matchesStatus =
        filters.status === "ALL" ||
        job.status === filters.status;

      const matchesSource =
        filters.source === "ALL" ||
        job.sourceName === filters.source;

      return matchesSearch && matchesStatus && matchesSource;
    });
  }, [filters]);
}