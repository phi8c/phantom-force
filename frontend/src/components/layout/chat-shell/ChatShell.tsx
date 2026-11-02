import type { ReactNode } from "react";

export function ChatShell({ sidebar, header, children, composer }: {
  sidebar: ReactNode; header: ReactNode; children: ReactNode; composer: ReactNode;
}) {
  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      <aside className="hidden w-64 shrink-0 flex-col border-r bg-muted/40 md:flex">{sidebar}</aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-16 shrink-0 flex-wrap items-center justify-between gap-3 border-b px-4 py-3 md:px-6">{header}</header>
        <main className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4 md:px-8">{children}</main>
        <footer className="shrink-0 px-4 pb-4 pt-2 md:px-8">{composer}</footer>
      </div>
    </div>
  );
}
