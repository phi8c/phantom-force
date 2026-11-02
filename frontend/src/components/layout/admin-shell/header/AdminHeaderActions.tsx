import type { ReactNode } from "react";
import Link from "next/link";
import { Bell, Search, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";

interface AdminHeaderActionsProps {
  accountAction?: ReactNode;
}

export function AdminHeaderActions({
  accountAction,
}: AdminHeaderActionsProps) {
  return (
    <div className="flex items-center gap-2">
      <Link href="/chat" className="inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-muted">
        <MessageSquare className="size-4" /> Chat
      </Link>
      <Button
        variant="ghost"
        size="icon"
        aria-label="Search"
      >
        <Search />
      </Button>

      <Button
        variant="ghost"
        size="icon"
        aria-label="Notifications"
      >
        <Bell />
      </Button>

      <div className="ml-2">
        {accountAction ?? (
          <div className="flex size-8 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
            A
          </div>
        )}
      </div>
    </div>
  );
}
