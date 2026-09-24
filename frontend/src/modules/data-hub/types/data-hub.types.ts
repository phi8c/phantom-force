export type DataHubNodeType =
  | "site"
  | "drive"
  | "folder"
  | "file";

export interface DataHubBrowseNode {
  id: string;
  name: string;
  type: DataHubNodeType;
  has_children: boolean;
  provider: string;
  locator: Record<string, unknown>;
}

export interface DataHubBrowseResponse {
  provider: string;
  nodes: DataHubBrowseNode[];
}
