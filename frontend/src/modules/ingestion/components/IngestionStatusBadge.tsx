import { cn } from "@/lib/utils";

import type { IngestionStatus } from "../types/ingestion.types";

interface IngestionStatusBadgeProps {
  status: IngestionStatus;
}

const statusConfig: Record<
  IngestionStatus,
  {
    label: string;
    className: string;
  }
> = {
  NOT_STARTED: {
    label: "Not started",
    className: "bg-muted text-muted-foreground",
  },
  READY: {
    label: "Ready",
    className: "bg-sky-500/10 text-sky-700 dark:text-sky-300",
  },
  QUEUED: {
    label: "Queued",
    className: "bg-muted text-muted-foreground",
  },
  RUNNING: {
    label: "Running",
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
  COMPLETED: {
    label: "Completed",
    className: "bg-green-500/10 text-green-600 dark:text-green-400",
  },
  FAILED: {
    label: "Failed",
    className: "bg-red-500/10 text-red-600 dark:text-red-400",
  },
  CANCELLED: {
    label: "Cancelled",
    className: "bg-orange-500/10 text-orange-600 dark:text-orange-400",
  },
};

export function IngestionStatusBadge({
  status,
}: IngestionStatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        config.className,
      )}
    >
      {config.label}
    </span>
  );
}
