import type { ReactNode } from "react";

import { KnowledgeSpaceAuthBoundary } from "@/modules/auth";

interface KnowledgeSpaceChatLayoutProps {
  children: ReactNode;
}

export default function KnowledgeSpaceChatLayout({
  children,
}: KnowledgeSpaceChatLayoutProps) {
  return (
    <KnowledgeSpaceAuthBoundary>
      {children}
    </KnowledgeSpaceAuthBoundary>
  );
}
