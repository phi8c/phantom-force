import { apiClient } from "@/lib/api/client";

import type { OrchestrationSnapshot } from "../types/orchestration.types";

export async function getOrchestrationSnapshot(
  jobId: string,
) {
  const response =
    await apiClient.get<OrchestrationSnapshot>(
      `/ingest/orchestration/jobs/${jobId}`,
    );

  return response.data;
}

export function createOrchestrationEventSource(
  jobId: string,
) {
  return new EventSource(
    `/backend-api/ingest/orchestration/jobs/${jobId}/events`,
  );
}
