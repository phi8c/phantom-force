"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  loginToKnowledgeSpace,
  loginToManagement,
  logout,
  logoutAllSessions,
  registerLocalUser,
  startKnowledgeSpaceOidc,
  startManagementOidc,
  verifyEmail,
  verifyMfa,
} from "../api";
import type {
  LocalLoginPayload,
  LocalLoginResponse,
  VerifyMfaPayload,
} from "../types";
import { authQueryKeys } from "./auth-query-keys";

export function useRegisterLocalUser() {
  return useMutation({
    mutationFn: registerLocalUser,
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: verifyEmail,
  });
}

export function useManagementLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: loginToManagement,
    onSuccess: (result) => refreshSessionAfterAuthentication(
      queryClient,
      result,
    ),
  });
}

export function useKnowledgeSpaceLogin(knowledgeSpaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LocalLoginPayload) =>
      loginToKnowledgeSpace(knowledgeSpaceId, payload),
    onSuccess: (result) => refreshSessionAfterAuthentication(
      queryClient,
      result,
    ),
  });
}

export function useStartManagementOidc() {
  return useMutation({
    mutationFn: startManagementOidc,
  });
}

export function useStartKnowledgeSpaceOidc(knowledgeSpaceId: string) {
  return useMutation({
    mutationFn: () => startKnowledgeSpaceOidc(knowledgeSpaceId),
  });
}

export function useVerifyMfa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: VerifyMfaPayload) => verifyMfa(payload),
    onSuccess: (result) => refreshSessionAfterAuthentication(
      queryClient,
      result,
    ),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.removeQueries({
        queryKey: authQueryKeys.currentUser(),
      });
    },
  });
}

export function useLogoutAllSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logoutAllSessions,
    onSuccess: () => {
      queryClient.removeQueries({
        queryKey: authQueryKeys.currentUser(),
      });
    },
  });
}

function refreshSessionAfterAuthentication(
  queryClient: ReturnType<typeof useQueryClient>,
  result: LocalLoginResponse,
) {
  if (result.status !== "success") {
    return;
  }

  return queryClient.invalidateQueries({
    queryKey: authQueryKeys.currentUser(),
  });
}
