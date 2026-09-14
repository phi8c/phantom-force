import { apiClient } from "@/lib/api/client";

import type { EmbeddingModel } from "../types";

export async function listEmbeddingModels(): Promise<
  EmbeddingModel[]
> {
  const response = await apiClient.get<EmbeddingModel[]>(
    "/embedding-models",
  );

  return response.data;
}
