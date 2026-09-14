export type DataHubProvider = {
  id: string;
  code: string;
  name: string;
  provider: string;
  configuration_schema: Record<string, unknown>;
};
