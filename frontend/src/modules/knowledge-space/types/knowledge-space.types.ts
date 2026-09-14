export type KnowledgeSpaceStatus = "ACTIVE" | "INACTIVE";

export type KnowledgeSpace = {
  id: string;
  enterprise_id: string;
  name: string;
  code: string;
  description: string | null;
  status: KnowledgeSpaceStatus | string;
  configuration: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
};

export type KnowledgeSpaceListItem = {
  id: string;
  enterprise_id: string;
  enterprise_name: string;
  name: string;
  code: string;
  description: string | null;
  status: KnowledgeSpaceStatus | string;
  created_at: string | null;
};

export type KnowledgeSpaceListResponse = {
  items: KnowledgeSpaceListItem[];
  page: number;
  page_size: number;
  total: number;
};

export type ListKnowledgeSpacesParams = {
  page?: number;
  page_size?: number;
  enterprise_id?: string | null;
  search?: string | null;
  status?: string | null;
};

export type CreateKnowledgeSpacePayload = {
  enterprise_id: string;
  name: string;
  code: string;
  description?: string | null;
  configuration?: Record<string, unknown>;
};

export type KnowledgeSpaceDataHubConfig = {
  id: string;
  knowledge_space_id: string;
  data_hub_provider_id: string;
  configuration: Record<string, unknown>;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type KnowledgeSpaceEmbeddingConfig = {
  id: string;
  knowledge_space_id: string;
  embedding_model_id: string;
  configuration: Record<string, unknown>;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type KnowledgeSpaceConfigEnvelope<TData> = {
  configured: boolean;
  data: TData | null;
};

export type SaveDataHubConfigPayload = {
  data_hub_provider_id: string;
  configuration: Record<string, unknown>;
  enabled: boolean;
};

export type SaveEmbeddingConfigPayload = {
  embedding_model_id: string;
  configuration: Record<string, unknown>;
  enabled: boolean;
};
