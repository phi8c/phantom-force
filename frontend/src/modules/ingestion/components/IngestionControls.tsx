"use client";

import { Plus, RefreshCcw, RotateCcw, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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

const sourceOptions = [
  "ALL",
  "SharePoint - HR",
  "SharePoint - Legal",
  "SharePoint - Product",
  "SharePoint - Finance",
  "SharePoint - Projects",
  "SharePoint - IT",
  "SharePoint - Management",
  "Company Wiki",
  "SharePoint - Security",
  "Azure Blob Storage",
  "SharePoint - Operations",
  "Local Folder",
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
          <div className="relative w-full md:max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />

            <Input
              value={filters.search}
              onChange={(event) =>
                onFilterChange({
                  search: event.target.value,
                })
              }
              placeholder="Search ingestion jobs..."
              className="h-8 pl-8 text-sm"
            />
          </div>

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

          <select
            value={filters.source}
            onChange={(event) =>
              onFilterChange({
                source: event.target.value,
              })
            }
            className="h-8 rounded-md border bg-background px-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            {sourceOptions.map((source) => (
              <option key={source} value={source}>
                {source === "ALL" ? "All sources" : source}
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