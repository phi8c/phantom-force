"use client";

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { createEnterprise } from "../api";
import { enterpriseQueryKeys } from "./use-enterprise-list";

export function useCreateEnterprise() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createEnterprise,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: enterpriseQueryKeys.all,
      });
    },
  });
}
