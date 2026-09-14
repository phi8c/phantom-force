import type { ReactNode } from "react";

import { AdminHeader } from "./header";
import { AdminMain } from "./main";
import { AdminSidebar } from "./sidebar";

interface AdminShellProps {
  children: ReactNode;
}

export function AdminShell({ children }: AdminShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AdminSidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <AdminHeader />

        <AdminMain>{children}</AdminMain>
      </div>
    </div>
  );
}