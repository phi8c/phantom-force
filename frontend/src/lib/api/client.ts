import axios from "axios";

function resolveApiBaseUrl() {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_URL;

  if (typeof window !== "undefined") {
    return "/backend-api";
  }

  if (!configuredBaseUrl) {
    return configuredBaseUrl;
  }

  return configuredBaseUrl;
}

export const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    "Content-Type": "application/json",
  },
});
