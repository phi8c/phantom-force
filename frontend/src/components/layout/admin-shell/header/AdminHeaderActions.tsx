import { Bell, Search } from "lucide-react";

import { Button } from "@/components/ui/button";

export function AdminHeaderActions() {
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

      <div className="ml-2 flex size-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
        A
      </div>
    </div>
  );
}