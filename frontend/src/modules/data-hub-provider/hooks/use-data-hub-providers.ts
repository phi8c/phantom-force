"use client";

import { useQuery } from "@tanstack/react-query";

import { listDataHubProviders } from "../api";

export const dataHubProviderQueryKeys = {
  all: ["data-hub-providers"] as const,
  list: () =>
    [...dataHubProviderQueryKeys.all, "list"] as const,
};

export function useDataHubProviders() {
  return useQuery({
    queryKey: dataHubProviderQueryKeys.list(),
    queryFn: listDataHubProviders,
  });
}
