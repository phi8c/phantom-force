import type { ReactNode } from "react";

interface AdminMainProps {
  children: ReactNode;
}

export function AdminMain({ children }: AdminMainProps) {
  return (
    <main className="min-h-0 flex-1 overflow-y-auto">
      {children}
    </main>
  );
}