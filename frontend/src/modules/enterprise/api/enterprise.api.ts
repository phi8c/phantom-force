import { apiClient } from "@/lib/api/client";

import type {
  CreateEnterprisePayload,
  Enterprise,
  EnterpriseOption,
  EnterpriseListResponse,
  UpdateEnterprisePayload,
} from "../types";

type ListEnterprisesParams = {
  limit?: number;
  cursor?: string | null;
};

export async function listEnterprises(
  params: ListEnterprisesParams = {},
): Promise<EnterpriseListResponse> {
  const response = await apiClient.get<EnterpriseListResponse>(
    "/enterprises",
    {
      params: {
        limit: params.limit,
        cursor: params.cursor ?? undefined,
      },
    },
  );

  return response.data;
}

export async function getEnterprise(
  id: string,
): Promise<Enterprise> {
  const response = await apiClient.get<Enterprise>(
    `/enterprises/${id}`,
  );

  return response.data;
}

export async function listEnterpriseOptions(): Promise<
  EnterpriseOption[]
> {
  const response = await apiClient.get<EnterpriseOption[]>(
    "/enterprises/options",
  );

  return response.data;
}

export async function createEnterprise(
  payload: CreateEnterprisePayload,
): Promise<Enterprise> {
  const response = await apiClient.post<Enterprise>(
    "/enterprises",
    payload,
  );

  return response.data;
}

export async function updateEnterprise(
  id: string,
  payload: UpdateEnterprisePayload,
): Promise<Enterprise> {
  const response = await apiClient.patch<Enterprise>(
    `/enterprises/${id}`,
    payload,
  );

  return response.data;
}
