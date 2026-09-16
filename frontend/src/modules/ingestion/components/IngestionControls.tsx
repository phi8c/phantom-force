"use client";

import { Plus, RefreshCcw, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";

import type {
  IngestionFilters,
  IngestionStatus,
} from "../types/ingestion.types";

interface IngestionControlsProps {
  filters: IngestionFilters;
  onFilterChange: (
    values: Partial<IngestionFilters>,
  ) => void;
  onReset: () => void;
  onRefresh: () => void;
  onCreate: () => void;
}

const statusOptions: Array<{
  value: IngestionStatus | "ALL";
  label: string;
}> = [
  {
    value: "ALL",
    label: "All statuses",
  },
  {
    value: "QUEUED",
    label: "Queued",
  },
  {
    value: "RUNNING",
    label: "Running",
  },
  {
    value: "COMPLETED",
    label: "Completed",
  },
  {
    value: "FAILED",
    label: "Failed",
  },
  {
    value: "CANCELLED",
    label: "Cancelled",
  },
];

export function IngestionControls({
  filters,
  onFilterChange,
  onReset,
  onRefresh,
  onCreate,
}: IngestionControlsProps) {
  return (
    <section className="border-b px-6 py-2">
      <div className="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-1 flex-col gap-2 md:flex-row">
          <select
            value={filters.status}
            onChange={(event) =>
              onFilterChange({
                status: event.target.value as
                  | IngestionStatus
                  | "ALL",
              })
            }
            className="h-8 rounded-md border bg-background px-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            {statusOptions.map((option) => (
              <option
                key={option.value}
                value={option.value}
              >
                {option.label}
              </option>
            ))}
          </select>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 px-2"
            onClick={onReset}
          >
            <RotateCcw className="size-3.5" />
            Reset
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8"
            onClick={onRefresh}
          >
            <RefreshCcw className="size-3.5" />
            Refresh
          </Button>

          <Button
            type="button"
            size="sm"
            className="h-8"
            onClick={onCreate}
          >
            <Plus className="size-3.5" />
            New ingestion
          </Button>
        </div>
      </div>
    </section>
  );
}
