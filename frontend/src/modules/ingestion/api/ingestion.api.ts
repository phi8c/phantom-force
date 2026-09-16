import type {
  CreateIngestionRequest,
  CreateIngestionResponse,
  IngestionConfigurationEnvelope,
  IngestionConfigurationRequest,
  IngestionJob,
  IngestionJobsPage,
  IngestionMasterOption,
  IngestionScopeEnvelope,
  IngestionScopeRequest,
} from "../types/ingestion.types";
import { apiClient } from "@/lib/api/client";

export const ingestionApi = {
  async getJobs(params?: {
    knowledgeSpaceId?: string;
    status?: string;
    limit?: number;
    cursor?: string | null;
  }): Promise<IngestionJobsPage> {
    const response = await apiClient.get<IngestionJobsPage>(
      "/ingest/jobs",
      {
        params: {
          knowledge_space_id: params?.knowledgeSpaceId,
          status: params?.status,
          limit: params?.limit ?? 20,
          cursor: params?.cursor,
        },
      },
    );

    return response.data;
  },

  async getJobById(id: string): Promise<IngestionJob> {
    throw new Error(`Ingestion detail API is not implemented yet: ${id}`);
  },

  async createJob(
    payload: CreateIngestionRequest,
  ): Promise<CreateIngestionResponse> {
    const response =
      await apiClient.post<CreateIngestionResponse>(
        "/ingest/jobs",
        {
          knowledge_space_id: payload.knowledgeSpaceId,
          trigger_type: payload.triggerType,
          is_build_graph: payload.isBuildGraph,
        },
      );

    return response.data;
  },

  async listExtractionEngines(): Promise<
    IngestionMasterOption[]
  > {
    const response =
      await apiClient.get<IngestionMasterOption[]>(
        "/ingest/master/extraction-engines",
      );

    return response.data;
  },

  async listChunkingStrategies(): Promise<
    IngestionMasterOption[]
  > {
    const response =
      await apiClient.get<IngestionMasterOption[]>(
        "/ingest/master/chunking-strategies",
      );

    return response.data;
  },

  async getConfiguration(
    jobId: string,
  ): Promise<IngestionConfigurationEnvelope> {
    const response =
      await apiClient.get<IngestionConfigurationEnvelope>(
        `/ingest/jobs/${jobId}/configuration`,
      );

    return response.data;
  },

  async saveConfiguration(
    jobId: string,
    payload: IngestionConfigurationRequest,
  ) {
    const response =
      await apiClient.put<IngestionConfigurationEnvelope>(
        `/ingest/jobs/${jobId}/configuration`,
        payload,
      );

    return response.data;
  },

  async getScope(
    jobId: string,
  ): Promise<IngestionScopeEnvelope> {
    const response =
      await apiClient.get<IngestionScopeEnvelope>(
        `/ingest/jobs/${jobId}/scope`,
      );

    return response.data;
  },

  async saveScope(
    jobId: string,
    payload: IngestionScopeRequest,
  ) {
    const response =
      await apiClient.put<IngestionScopeEnvelope>(
        `/ingest/jobs/${jobId}/scope`,
        payload,
      );

    return response.data;
  },

  async startJob(
    jobId: string,
    batchSize = 100,
  ): Promise<{ ingestion_job_id: string; status: string }> {
    const response = await apiClient.post<{
      ingestion_job_id: string;
      status: string;
    }>(
      `/ingest/jobs/${jobId}/start`,
      {
        batch_size: batchSize,
      },
    );

    return response.data;
  },

  async retryJob(id: string): Promise<void> {
    throw new Error(`Retry ingestion API is not implemented yet: ${id}`);
  },

  async cancelJob(id: string): Promise<void> {
    throw new Error(`Cancel ingestion API is not implemented yet: ${id}`);
  },
};
