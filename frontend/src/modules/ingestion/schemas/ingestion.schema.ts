import type { CreateIngestionRequest } from "../types/ingestion.types";

export function validateCreateIngestion(
  payload: CreateIngestionRequest,
): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!payload.knowledgeSpaceId.trim()) {
    errors.knowledgeSpaceId =
      "Knowledge Space is required.";
  }

  if (payload.triggerType !== "MANUAL") {
    errors.triggerType = "Trigger Type must be MANUAL.";
  }

  return errors;
}
