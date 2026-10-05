export {
  getCurrentUser,
  getKnowledgeSpaceAuthRequirement,
  loginToKnowledgeSpace,
  loginToManagement,
  logout,
  logoutAllSessions,
  registerLocalUser,
  startKnowledgeSpaceOidc,
  startManagementOidc,
  verifyEmail,
  verifyMfa,
} from "./api";

export type {
  AuthActionResponse,
  AuthenticationContextType,
  AuthFlowStatus,
  AuthProvider,
  CurrentUser,
  KnowledgeSpaceAuthRequirement,
  LocalLoginPayload,
  LocalLoginResponse,
  MessageResponse,
  OidcStartResponse,
  RegisterLocalUserPayload,
  VerifyEmailPayload,
  VerifyMfaPayload,
} from "./types";

export {
  authQueryKeys,
  useCurrentUser,
  useKnowledgeSpaceAuthRequirement,
  useKnowledgeSpaceLogin,
  useLogout,
  useLogoutAllSessions,
  useManagementLogin,
  useRegisterLocalUser,
  useStartKnowledgeSpaceOidc,
  useStartManagementOidc,
  useVerifyEmail,
  useVerifyMfa,
} from "./hooks";

export {
  AuthCallbackView,
  AuthLoadingState,
  KnowledgeSpaceSessionHeader,
  KnowledgeSpaceAuthBoundary,
  KnowledgeSpaceLoginView,
  LocalLoginForm,
  ManagementAuthBoundary,
  ManagementLoginView,
  MfaChallengeForm,
  MicrosoftLoginButton,
  RegistrationView,
  SessionMenu,
  VerifyEmailView,
} from "./components";

export {
  getAuthErrorMessage,
  isUnauthorizedAuthError,
} from "./auth-errors";

export {
  getSessionHomePath,
  isKnowledgeSpaceSession,
  isManagementSession,
} from "./session-context";
