import { apiClient } from "@/lib/api/client";

import type {
  DataHubBrowseNode,
  DataHubBrowseResponse,
} from "../types";

export async function browseDataHubRoot(
  knowledgeSpaceId: string,
) {
  const response = await apiClient.get<DataHubBrowseResponse>(
    `/data-hub/knowledge-spaces/${encodeURIComponent(knowledgeSpaceId)}/browse`,
  );

  return response.data;
}

export async function browseDataHubChildren(
  knowledgeSpaceId: string,
  locator: Record<string, unknown>,
) {
  const response = await apiClient.post<DataHubBrowseResponse>(
    `/data-hub/knowledge-spaces/${encodeURIComponent(knowledgeSpaceId)}/browse`,
    { locator },
  );

  return response.data;
}

export async function listSharePointSites() {
  const response =
    await apiClient.get<DataHubBrowseNode[]>(
      "/data-hub/sharepoint/sites",
    );

  return response.data;
}

export async function listSharePointDrives(
  siteId: string,
) {
  const response =
    await apiClient.get<DataHubBrowseNode[]>(
      `/data-hub/sharepoint/sites/${siteId}/drives`,
    );

  return response.data;
}

export async function listSharePointDriveChildren(
  siteId: string,
  driveId: string,
) {
  const response =
    await apiClient.get<DataHubBrowseNode[]>(
      `/data-hub/sharepoint/sites/${siteId}/drives/${driveId}/children`,
    );

  return response.data;
}

export async function listSharePointFolderChildren(
  siteId: string,
  driveId: string,
  folderId: string,
) {
  const response =
    await apiClient.get<DataHubBrowseNode[]>(
      `/data-hub/sharepoint/sites/${siteId}/drives/${driveId}/items/${folderId}/children`,
    );

  return response.data;
}
