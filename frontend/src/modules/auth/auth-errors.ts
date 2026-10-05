import axios from "axios";

interface ApiErrorBody {
  detail?: string;
}

export function isUnauthorizedAuthError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 401;
}

export function getAuthErrorMessage(
  error: unknown,
  fallback = "Authentication could not be completed.",
): string {
  if (!axios.isAxiosError<ApiErrorBody>(error)) {
    return fallback;
  }

  const detail = error.response?.data?.detail;
  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (!error.response) {
    return "Unable to reach the authentication service.";
  }

  return fallback;
}
