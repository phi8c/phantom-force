import { apiClient } from "@/lib/api/client";

import type {
  CreateKnowledgeSpacePayload,
  KnowledgeSpace,
  KnowledgeSpaceConfigEnvelope,
  KnowledgeSpaceDataHubConfig,
  KnowledgeSpaceEmbeddingConfig,
  KnowledgeSpaceListResponse,
  ListKnowledgeSpacesParams,
  SaveDataHubConfigPayload,
  SaveEmbeddingConfigPayload,
} from "../types";

export async function listKnowledgeSpaces(
  params: ListKnowledgeSpacesParams = {},
): Promise<KnowledgeSpaceListResponse> {
  const response =
    await apiClient.get<KnowledgeSpaceListResponse>(
      "/knowledge-spaces",
      {
        params: {
          page: params.page,
          page_size: params.page_size,
          enterprise_id: params.enterprise_id ?? undefined,
          search: params.search ?? undefined,
          status: params.status ?? undefined,
        },
      },
    );

  return response.data;
}

export async function createKnowledgeSpace(
  payload: CreateKnowledgeSpacePayload,
): Promise<KnowledgeSpace> {
  const response = await apiClient.post<KnowledgeSpace>(
    "/knowledge-spaces",
    payload,
  );

  return response.data;
}

export async function getKnowledgeSpace(
  id: string,
): Promise<KnowledgeSpace> {
  const response = await apiClient.get<KnowledgeSpace>(
    `/knowledge-spaces/${id}`,
  );

  return response.data;
}

export async function getKnowledgeSpaceDataHubConfig(
  knowledgeSpaceId: string,
): Promise<
  KnowledgeSpaceConfigEnvelope<KnowledgeSpaceDataHubConfig>
> {
  const response = await apiClient.get<
    KnowledgeSpaceConfigEnvelope<KnowledgeSpaceDataHubConfig>
  >(`/knowledge-spaces/${knowledgeSpaceId}/data-hub`);

  return response.data;
}

export async function saveKnowledgeSpaceDataHubConfig(
  knowledgeSpaceId: string,
  payload: SaveDataHubConfigPayload,
): Promise<KnowledgeSpaceDataHubConfig> {
  const response =
    await apiClient.put<KnowledgeSpaceDataHubConfig>(
      `/knowledge-spaces/${knowledgeSpaceId}/data-hub`,
      payload,
    );

  return response.data;
}

export async function getKnowledgeSpaceEmbeddingConfig(
  knowledgeSpaceId: string,
): Promise<
  KnowledgeSpaceConfigEnvelope<KnowledgeSpaceEmbeddingConfig>
> {
  const response = await apiClient.get<
    KnowledgeSpaceConfigEnvelope<KnowledgeSpaceEmbeddingConfig>
  >(`/knowledge-spaces/${knowledgeSpaceId}/embedding`);

  return response.data;
}

export async function saveKnowledgeSpaceEmbeddingConfig(
  knowledgeSpaceId: string,
  payload: SaveEmbeddingConfigPayload,
): Promise<KnowledgeSpaceEmbeddingConfig> {
  const response =
    await apiClient.put<KnowledgeSpaceEmbeddingConfig>(
      `/knowledge-spaces/${knowledgeSpaceId}/embedding`,
      payload,
    );

  return response.data;
}
