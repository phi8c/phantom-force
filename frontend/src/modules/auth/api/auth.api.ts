import { apiClient } from "@/lib/api/client";

import type {
  AuthActionResponse,
  CurrentUser,
  KnowledgeSpaceAuthRequirement,
  LocalLoginPayload,
  LocalLoginResponse,
  MessageResponse,
  OidcStartResponse,
  RegisterLocalUserPayload,
  VerifyEmailPayload,
  VerifyMfaPayload,
} from "../types";

export async function registerLocalUser(
  payload: RegisterLocalUserPayload,
): Promise<MessageResponse> {
  const response = await apiClient.post<MessageResponse>(
    "/auth/register",
    payload,
  );
  return response.data;
}

export async function verifyEmail(
  payload: VerifyEmailPayload,
): Promise<MessageResponse> {
  const response = await apiClient.post<MessageResponse>(
    "/auth/verify-email",
    payload,
  );
  return response.data;
}

export async function getKnowledgeSpaceAuthRequirement(
  knowledgeSpaceId: string,
): Promise<KnowledgeSpaceAuthRequirement> {
  const response = await apiClient.get<KnowledgeSpaceAuthRequirement>(
    `/auth/knowledge-spaces/${encodeURIComponent(knowledgeSpaceId)}/requirement`,
  );
  return response.data;
}

export async function loginToManagement(
  payload: LocalLoginPayload,
): Promise<LocalLoginResponse> {
  const response = await apiClient.post<LocalLoginResponse>(
    "/auth/management/login/local",
    payload,
  );
  return response.data;
}

export async function loginToKnowledgeSpace(
  knowledgeSpaceId: string,
  payload: LocalLoginPayload,
): Promise<LocalLoginResponse> {
  const response = await apiClient.post<LocalLoginResponse>(
    `/auth/knowledge-spaces/${encodeURIComponent(knowledgeSpaceId)}/login/local`,
    payload,
  );
  return response.data;
}

export async function startManagementOidc(): Promise<OidcStartResponse> {
  const response = await apiClient.post<OidcStartResponse>(
    "/auth/management/login/entra/start",
  );
  return response.data;
}

export async function startKnowledgeSpaceOidc(
  knowledgeSpaceId: string,
): Promise<OidcStartResponse> {
  const response = await apiClient.post<OidcStartResponse>(
    `/auth/knowledge-spaces/${encodeURIComponent(knowledgeSpaceId)}/login/entra/start`,
  );
  return response.data;
}

export async function verifyMfa(
  payload: VerifyMfaPayload,
): Promise<LocalLoginResponse> {
  const response = await apiClient.post<LocalLoginResponse>(
    "/auth/mfa/verify",
    payload,
  );
  return response.data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>("/auth/me");
  return response.data;
}

export async function logout(): Promise<AuthActionResponse> {
  const response = await apiClient.post<AuthActionResponse>("/auth/logout");
  return response.data;
}

export async function logoutAllSessions(): Promise<AuthActionResponse> {
  const response = await apiClient.post<AuthActionResponse>(
    "/auth/logout-all",
  );
  return response.data;
}
