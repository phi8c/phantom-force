export type DataHubNodeType =
  | "site"
  | "drive"
  | "folder"
  | "file";

export interface DataHubBrowseNode {
  id: string;
  name: string;
  type: DataHubNodeType;
  site_id: string | null;
  drive_id: string | null;
  parent_id: string | null;
  has_children: boolean;
}
