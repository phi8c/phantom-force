"use client";

import { useEffect, useRef, useState } from "react";
import { sendChatQuestion } from "../api/chat.api";
import { getChatErrorMessage } from "../services/chat.service";
import type { Conversation } from "../types/chat.types";

// The API accepts one question per request. Conversation history is UI state only.
export function useChat(knowledgeSpaceId: string) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  const activeConversation = conversations.find((item) => item.id === activeId);

  function newConversation() {
    if (controller.current) return;
    setActiveId(null);
    setError(null);
  }

  function selectConversation(id: string) {
    if (controller.current) return;
    setActiveId(id);
    setError(null);
  }

  async function send(question: string) {
    const content = question.trim();
    if (!content || !knowledgeSpaceId || controller.current) return false;
    const requestController = new AbortController();
    controller.current = requestController;
    setPending(true);
    setError(null);
    const conversationId = activeId ?? crypto.randomUUID();
    const message = { id: crypto.randomUUID(), role: "user" as const, content };
    setConversations((items) => activeId
      ? items.map((item) => item.id === conversationId ? { ...item, messages: [...item.messages, message] } : item)
      : [{ id: conversationId, knowledgeSpaceId, title: content.slice(0, 70), messages: [message] }, ...items]);
    setActiveId(conversationId);
    try {
      const response = await sendChatQuestion({ knowledge_space_id: knowledgeSpaceId, question: content }, requestController.signal);
      setConversations((items) => items.map((item) => item.id === conversationId
        ? { ...item, messages: [...item.messages, { id: crypto.randomUUID(), role: "assistant", content: response.answer, response }] }
        : item));
      return true;
    } catch (caught) {
      if (!requestController.signal.aborted) setError(getChatErrorMessage(caught));
      return false;
    } finally {
      controller.current = null;
      setPending(false);
    }
  }

  return { conversations, activeId, activeConversation, pending, error, send, newConversation, selectConversation };
}
