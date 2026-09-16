export type OrchestrationStage =
  | "DISCOVERY"
  | "DOWNLOAD"
  | "EXTRACTION"
  | "CHUNKING"
  | "EMBEDDING"
  | "CLASSIFICATION";

export interface OrchestrationJobSummary {
  id: string;
  total_batches: number;
  total_files: number;
  completed_files: number;
  failed_files: number;
  processing_batches: number;
  completed_batches: number;
  failed_batches: number;
}

export interface OrchestrationBatch {
  id: string;
  ingestion_job_id: string;
  batch_index: number;
  status: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  created_at: string | null;
  updated_at: string | null;
  stages?: Record<string, Record<string, number>>;
}

export interface OrchestrationSnapshot {
  job: OrchestrationJobSummary;
  batches: OrchestrationBatch[];
  stages: Record<string, Record<string, number>>;
}

export interface OrchestrationEvent {
  sequence_no: number;
  ingestion_job_id: string;
  ingestion_batch_id: string | null;
  document_id: string | null;
  event_type: string;
  stage: string | null;
  status: string | null;
  payload: Record<string, unknown> | null;
  created_at: string | null;
}
