"use client";

import { useState, type FormEvent } from "react";
import { ArrowUp, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatComposerProps {
  pending: boolean;
  onSend: (question: string) => Promise<boolean>;
}

export function ChatComposer({ pending, onSend }: ChatComposerProps) {
  const [draft, setDraft] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || pending) return;
    const question = draft;
    setDraft("");
    if (!await onSend(question)) setDraft(question);
  }
  return (
    <form onSubmit={submit} className="mx-auto w-full max-w-3xl">
      <div className="rounded-3xl border bg-background p-3 shadow-sm focus-within:ring-2 focus-within:ring-ring/30">
        <textarea
          aria-label="Câu hỏi" placeholder="Hỏi về dữ liệu của bạn…" value={draft}
          onChange={(event) => setDraft(event.target.value)} disabled={pending} rows={2}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
          className="max-h-48 min-h-16 w-full resize-y bg-transparent px-2 py-1 text-sm outline-none disabled:opacity-60"
        />
        <div className="flex items-center justify-between pl-2">
          <span className="text-xs text-muted-foreground">Shift + Enter để xuống dòng</span>
          <Button type="submit" size="icon" className="rounded-full" disabled={pending || !draft.trim()} aria-label="Gửi câu hỏi">
            {pending ? <LoaderCircle className="animate-spin" /> : <ArrowUp />}
          </Button>
        </div>
      </div>
      <p className="mt-2 text-center text-xs text-muted-foreground">Câu trả lời được tạo từ knowledge space đã chọn. Hãy kiểm tra lại thông tin quan trọng.</p>
    </form>
  );
}
