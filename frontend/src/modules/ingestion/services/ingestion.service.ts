import { ingestionApi } from "../api/ingestion.api";
import { mockIngestionJobs } from "../mocks/ingestion.mock";
import type {
  CreateIngestionRequest,
  CreateIngestionResponse,
  IngestionJob,
  IngestionJobsPage,
} from "../types/ingestion.types";

const USE_MOCK_DATA = true;

export const ingestionService = {
  async getJobs(): Promise<IngestionJobsPage> {
    if (USE_MOCK_DATA) {
      return Promise.resolve({
        items: mockIngestionJobs,
        next_cursor: null,
        has_more: false,
      });
    }

    return ingestionApi.getJobs();
  },

  async getJobById(id: string): Promise<IngestionJob | undefined> {
    if (USE_MOCK_DATA) {
      return Promise.resolve(
        mockIngestionJobs.find((job) => job.id === id),
      );
    }

    return ingestionApi.getJobById(id);
  },

  async createJob(
    payload: CreateIngestionRequest,
  ): Promise<CreateIngestionResponse> {
    return ingestionApi.createJob(payload);
  },

  async retryJob(id: string): Promise<void> {
    return ingestionApi.retryJob(id);
  },

  async cancelJob(id: string): Promise<void> {
    return ingestionApi.cancelJob(id);
  },
};
