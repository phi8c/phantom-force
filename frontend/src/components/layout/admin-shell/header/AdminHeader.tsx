import type { ReactNode } from "react";

import { AdminHeaderActions } from "./AdminHeaderActions";
import { AdminHeaderTitle } from "./AdminHeaderTitle";

interface AdminHeaderProps {
  accountAction?: ReactNode;
}

export function AdminHeader({ accountAction }: AdminHeaderProps) {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b bg-background px-6">
      <AdminHeaderTitle />

      <AdminHeaderActions accountAction={accountAction} />
    </header>
  );
}
