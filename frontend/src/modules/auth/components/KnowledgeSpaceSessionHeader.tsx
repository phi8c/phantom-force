"use client";

import { Database } from "lucide-react";

import { SessionMenu } from "./SessionMenu";

interface KnowledgeSpaceSessionHeaderProps {
  knowledgeSpaceId: string;
}

export function KnowledgeSpaceSessionHeader({
  knowledgeSpaceId,
}: KnowledgeSpaceSessionHeaderProps) {
  return (
    <header className="flex h-12 items-center justify-between border-b px-4 sm:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <Database className="size-4 shrink-0" />
        <span className="truncate text-sm font-medium">Knowledge Space</span>
      </div>
      <SessionMenu
        signedOutPath={`/chat/${encodeURIComponent(knowledgeSpaceId)}/login`}
      />
    </header>
  );
}
