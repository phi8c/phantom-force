import { apiClient } from "@/lib/api/client";

import type { DataHubProvider } from "../types";

export async function listDataHubProviders(): Promise<
  DataHubProvider[]
> {
  const response = await apiClient.get<DataHubProvider[]>(
    "/data-hub-providers",
  );

  return response.data;
}
