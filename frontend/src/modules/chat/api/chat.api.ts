import { apiClient } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "../types/chat.types";

export async function sendChatQuestion(request: ChatRequest, signal?: AbortSignal) {
  const { data } = await apiClient.post<ChatResponse>("/chat", request, {
    signal,
    timeout: 10 * 60 * 1000,
  });
  return data;
}
