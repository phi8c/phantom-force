import type { ReactNode } from "react";
import { Bell, Search } from "lucide-react";

import { Button } from "@/components/ui/button";

interface AdminHeaderActionsProps {
  accountAction?: ReactNode;
}

export function AdminHeaderActions({
  accountAction,
}: AdminHeaderActionsProps) {
  return (
    <div className="flex items-center gap-2">
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
