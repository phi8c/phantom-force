import type { CreateIngestionRequest } from "../types/ingestion.types";

export function validateCreateIngestion(
  payload: CreateIngestionRequest,
): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!payload.name.trim()) {
    errors.name = "Ingestion name is required.";
  }

  if (!payload.sourceId.trim()) {
    errors.sourceId = "Source is required.";
  }

  if (!payload.knowledgeSpaceId.trim()) {
    errors.knowledgeSpaceId =
      "Knowledge Space is required.";
  }

  return errors;
}