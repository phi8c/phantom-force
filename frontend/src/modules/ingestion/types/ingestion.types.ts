export type IngestionStatus =
  | "READY"
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "NOT_STARTED";

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
  knowledge_space_id: string;
  trigger_type: string;
  status: IngestionStatus | null;
  is_build_graph: boolean;
  total_files: number;
  completed_files: number;
  failed_files: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
  scope_type: string | null;
  scope_data: Record<string, unknown> | null;
}

export interface IngestionFilters {
  search: string;
  status: IngestionStatus | "ALL";
  source: string;
}

export interface IngestionJobsPage {
  items: IngestionJob[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface CreateIngestionRequest {
  knowledgeSpaceId: string;
  triggerType: "MANUAL";
  isBuildGraph: boolean;
}

export interface CreateIngestionResponse {
  ingestion_job_id: string;
}

export interface IngestionMasterOption {
  id: string;
  code: string;
  name: string;
  provider?: string | null;
  configuration: Record<string, unknown>;
}

export interface IngestionConfigurationRequest {
  extraction_engine_code: string;
  chunking_strategy_code: string;
  model_set_code: string | null;
  is_classification: boolean;
  configuration: Record<string, unknown>;
}

export interface IngestionConfigurationEnvelope {
  configured: boolean;
  data: {
    ingestion_job_id: string;
    extraction_engine_id: string;
    chunking_strategy_id: string;
    model_set_id: string | null;
    is_classification: boolean;
    configuration: Record<string, unknown>;
  } | null;
}

export interface GenericIngestionScopeRoot {
  locator: Record<string, unknown>;
}

export interface LegacySharePointScopeRoot {
  site_id: string;
  drive_id: string;
  folder_id: string | null;
}

export type IngestionScopeRoot =
  | GenericIngestionScopeRoot
  | LegacySharePointScopeRoot;

export interface IngestionScopeRequest {
  scope_type: "SELECTED_ROOTS";
  scope_data: {
    roots: IngestionScopeRoot[];
  };
}

export interface IngestionScopeEnvelope {
  configured: boolean;
  data: {
    ingestion_job_id: string;
    scope_type: string | null;
    scope_data: IngestionScopeRequest["scope_data"] | null;
  } | null;
}
