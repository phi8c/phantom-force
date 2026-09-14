"use client";

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { createKnowledgeSpace } from "../api";
import { knowledgeSpaceQueryKeys } from "./use-knowledge-space-list";

export function useCreateKnowledgeSpace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createKnowledgeSpace,
    onSuccess: (knowledgeSpace) => {
      void queryClient.invalidateQueries({
        queryKey: knowledgeSpaceQueryKeys.all,
      });
      queryClient.setQueryData(
        knowledgeSpaceQueryKeys.detail(knowledgeSpace.id),
        knowledgeSpace,
      );
    },
  });
}
