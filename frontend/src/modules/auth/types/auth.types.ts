export type AuthProvider = "local" | "entra" | "google";

export type AuthenticationContextType =
  | "MANAGEMENT"
  | "KNOWLEDGE_SPACE";

export type AuthFlowStatus =
  | "success"
  | "mfa_required"
  | "mfa_enrollment_required";

export interface RegisterLocalUserPayload {
  email: string;
  password: string;
}

export interface MessageResponse {
  message: string;
}

export interface VerifyEmailPayload {
  token: string;
}

export interface LocalLoginPayload {
  email: string;
  password: string;
}

export interface LocalLoginResponse {
  status: AuthFlowStatus;
  mfa_challenge_id: string | null;
}

export interface OidcStartResponse {
  authorization_url: string;
}

export interface KnowledgeSpaceAuthRequirement {
  auth_method: AuthProvider;
  require_mfa: boolean;
}

export interface VerifyMfaPayload {
  challenge_id: string;
  code: string;
}

export interface CurrentUser {
  user_id: string;
  email: string;
  context_type: AuthenticationContextType;
  auth_method: AuthProvider;
  knowledge_space_id: string | null;
  authenticated_at: string;
  mfa_verified: boolean;
}

export interface AuthActionResponse {
  success: boolean;
}
