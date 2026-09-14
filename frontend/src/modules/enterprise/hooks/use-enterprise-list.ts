"use client";

import { useQuery } from "@tanstack/react-query";

import {
  listEnterpriseOptions,
  listEnterprises,
} from "../api";

export const enterpriseQueryKeys = {
  all: ["enterprises"] as const,
  options: () =>
    [...enterpriseQueryKeys.all, "options"] as const,
  list: (cursor: string | null, limit: number) =>
    [...enterpriseQueryKeys.all, "list", cursor, limit] as const,
};

export function useEnterpriseList({
  cursor,
  limit,
}: {
  cursor: string | null;
  limit: number;
}) {
  return useQuery({
    queryKey: enterpriseQueryKeys.list(cursor, limit),
    queryFn: () =>
      listEnterprises({
        cursor,
        limit,
    }),
  });
}

export function useEnterpriseOptions() {
  return useQuery({
    queryKey: enterpriseQueryKeys.options(),
    queryFn: listEnterpriseOptions,
  });
}
