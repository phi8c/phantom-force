import { apiClient } from "@/lib/api/client";

import type { DataHubBrowseNode } from "../types";

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
