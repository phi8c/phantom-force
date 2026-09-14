export type EmbeddingModel = {
  id: string;
  code: string;
  name: string;
  provider: string;
  dimension: number;
  configuration: Record<string, unknown>;
};
