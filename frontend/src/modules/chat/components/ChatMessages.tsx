"use client";

import { useEffect, useRef } from "react";
import { Sparkles } from "lucide-react";
import type { ChatMessage } from "../types/chat.types";
import { StructuredResultView } from "./StructuredResultView";

export function ChatMessages({ messages, pending }: { messages: ChatMessage[]; pending: boolean }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, pending]);
  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 py-8" role="log" aria-label="Nội dung hội thoại" aria-live="polite">
      {messages.map((message) => (
        <article key={message.id} className={message.role === "user" ? "flex justify-end" : "flex gap-3"}>
          {message.role === "assistant" && <Sparkles className="mt-1 size-5 shrink-0 text-primary" />}
          <div className={message.role === "user" ? "max-w-[85%] rounded-3xl bg-muted px-5 py-3" : "min-w-0 flex-1 py-1"}>
            <p className="whitespace-pre-wrap break-words text-sm leading-7">{message.content}</p>
            {message.response?.structured_results?.map((result, index) => <StructuredResultView key={index} result={result} />)}
            {message.response && (
              <details className="mt-4 rounded-xl border p-3 text-xs text-muted-foreground">
                <summary className="cursor-pointer">Thông tin truy xuất · {message.response.information.length} mục tri thức</summary>
                <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words">{JSON.stringify({ intent: message.response.intent, knowledge_requests: message.response.knowledge_requests, information: message.response.information }, null, 2)}</pre>
              </details>
            )}
          </div>
        </article>
      ))}
      {pending && <div role="status" className="flex items-center gap-3 text-sm text-muted-foreground"><Sparkles className="size-5 animate-pulse" />Đang tìm kiếm tri thức và tạo câu trả lời…</div>}
      <div ref={end} />
    </div>
  );
}
