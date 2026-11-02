"use client";

import Link from "next/link";
import { MessageSquare, Plus, Settings2, Sparkles } from "lucide-react";
import { ChatShell } from "@/components/layout/chat-shell/ChatShell";
import { Button } from "@/components/ui/button";
import { SessionMenu, useCurrentUser, isManagementSession } from "@/modules/auth";
import { useKnowledgeSpaceDetail } from "@/modules/knowledge-space";
import { useChat } from "../hooks/use-chat";
import { ChatComposer } from "./ChatComposer";
import { ChatMessages } from "./ChatMessages";

export function ChatWorkspace({ knowledgeSpaceId }: { knowledgeSpaceId: string }) {
  const chat = useChat(knowledgeSpaceId);
  const session = useCurrentUser();
  const management = isManagementSession(session.data);
  const space = useKnowledgeSpaceDetail(management ? knowledgeSpaceId : null);
  const spaceName = space.data?.name ?? `Knowledge Space · ${knowledgeSpaceId.slice(0, 8)}`;
  const messages = chat.activeConversation?.messages ?? [];
  return (
    <ChatShell
      sidebar={<>
        <div className="flex items-center gap-2 px-5 py-6 text-lg font-semibold"><Sparkles className="size-5" /> Phantom Force</div>
        <div className="px-3"><Button variant="outline" className="w-full justify-start" onClick={chat.newConversation} disabled={chat.pending}><Plus /> Cuộc trò chuyện mới</Button></div>
        <p className="px-5 pb-2 pt-8 text-xs font-medium text-muted-foreground">Hội thoại trong phiên này</p>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3" aria-label="Hội thoại">
          {chat.conversations.map((item) => <button key={item.id} disabled={chat.pending} onClick={() => chat.selectConversation(item.id)} className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-muted disabled:opacity-60 ${item.id === chat.activeId ? "bg-muted" : ""}`}><MessageSquare className="size-4 shrink-0" /><span className="truncate">{item.title}</span></button>)}
          {!chat.conversations.length && <p className="px-2 py-3 text-xs text-muted-foreground">Bắt đầu bằng một câu hỏi.</p>}
        </nav>
        <div className="border-t p-4 text-xs text-muted-foreground">Hội thoại tạm thời, được giữ khi bạn ở trang này.</div>
      </>}
      header={<>
        <div className="min-w-0"><p className="font-semibold">Phantom Force</p><p className="max-w-56 truncate text-xs text-muted-foreground">{spaceName}</p></div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={chat.newConversation} disabled={chat.pending} aria-label="Cuộc trò chuyện mới"><Plus /></Button>
          {management && <><Link href="/chat" className="text-xs text-muted-foreground hover:text-foreground">Đổi space</Link><Link href="/admin" className="inline-flex items-center gap-1 text-xs"><Settings2 className="size-4" /> Admin</Link></>}
          <SessionMenu signedOutPath={management ? "/admin/login" : `/chat/${knowledgeSpaceId}/login`} />
        </div>
        <select aria-label="Chọn hội thoại" className="w-full rounded-lg border bg-background p-2 text-sm md:hidden" value={chat.activeId ?? ""} disabled={chat.pending} onChange={(event) => event.target.value ? chat.selectConversation(event.target.value) : chat.newConversation()}><option value="">Cuộc trò chuyện mới</option>{chat.conversations.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
      </>}
      composer={<><div className="mx-auto max-w-3xl">{chat.error && <p role="alert" className="mb-3 rounded-xl bg-destructive/10 p-3 text-sm text-destructive">{chat.error}</p>}</div><ChatComposer pending={chat.pending} onSend={chat.send} /></>}
    >
      {messages.length ? <ChatMessages messages={messages} pending={chat.pending} /> : <div className="m-auto w-full max-w-2xl py-12 text-center"><div className="mx-auto mb-6 flex size-14 items-center justify-center rounded-2xl bg-primary/10"><Sparkles className="size-7 text-primary" /></div><h1 className="text-3xl font-semibold tracking-tight">Bạn muốn tìm hiểu điều gì?</h1><p className="mt-4 text-sm leading-6 text-muted-foreground">Tra cứu, so sánh và khám phá tri thức trong {spaceName}.</p><div className="mt-8 grid gap-3 sm:grid-cols-2">{["Tóm tắt những nội dung chính trong kho tri thức", "Những đối tượng nào được đề cập trong tài liệu?"].map((question) => <button key={question} onClick={() => void chat.send(question)} disabled={chat.pending} className="rounded-2xl border p-4 text-left text-sm leading-6 transition-colors hover:bg-muted">{question}</button>)}</div></div>}
    </ChatShell>
  );
}
