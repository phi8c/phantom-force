export type IngestionStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type IngestionStage =
  | "DISCOVERY"
  | "DOWNLOAD"
  | "EXTRACT"
  | "CHUNK"
  | "EMBEDDING"
  | "CLASSIFICATION"
  | "COMPLETED";

export interface IngestionJob {
  id: string;
  name: string;
  sourceName: string;
  knowledgeSpaceName: string;
  documentCount: number;
  processedDocumentCount: number;
  currentStage: IngestionStage;
  status: IngestionStatus;
  startedAt: string;
  finishedAt?: string;
  createdBy: string;
  errorMessage?: string;
}

export interface IngestionFilters {
  search: string;
  status: IngestionStatus | "ALL";
  source: string;
}

export interface CreateIngestionRequest {
  name: string;
  sourceId: string;
  knowledgeSpaceId: string;
}