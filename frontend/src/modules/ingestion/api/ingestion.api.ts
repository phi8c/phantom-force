import type {
  CreateIngestionRequest,
  IngestionJob,
} from "../types/ingestion.types";

export const ingestionApi = {
  async getJobs(): Promise<IngestionJob[]> {
    throw new Error("Ingestion API is not implemented yet.");
  },

  async getJobById(id: string): Promise<IngestionJob> {
    throw new Error(`Ingestion detail API is not implemented yet: ${id}`);
  },

  async createJob(
    payload: CreateIngestionRequest,
  ): Promise<IngestionJob> {
    throw new Error(
      `Create ingestion API is not implemented yet: ${payload.name}`,
    );
  },

  async retryJob(id: string): Promise<void> {
    throw new Error(`Retry ingestion API is not implemented yet: ${id}`);
  },

  async cancelJob(id: string): Promise<void> {
    throw new Error(`Cancel ingestion API is not implemented yet: ${id}`);
  },
};