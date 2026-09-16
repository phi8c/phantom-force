"use client";

import {
  MoreHorizontal,
  Play,
  Settings,
} from "lucide-react";

import {
  DataTable,
  type DataTableColumn,
} from "@/components/shared/data-table";
import { Button } from "@/components/ui/button";

import { IngestionStatusBadge } from "./IngestionStatusBadge";
import { useStartIngestionJob } from "../hooks/use-ingestion-config";
import type { IngestionJob } from "../types/ingestion.types";

interface IngestionJobsTableProps {
  jobs: IngestionJob[];
  loading?: boolean;
  onRowClick: (job: IngestionJob) => void;
  onConfigure: (job: IngestionJob) => void;
  onStarted?: (job: IngestionJob) => void;
}

export function IngestionJobsTable({
  jobs,
  loading = false,
  onRowClick,
  onConfigure,
  onStarted,
}: IngestionJobsTableProps) {
  const startMutation = useStartIngestionJob();

  const columns: DataTableColumn<IngestionJob>[] = [
    {
      id: "job",
      header: "Job",
      width: "260px",
      cell: (job) => (
        <div className="min-w-[220px]">
          <p className="font-medium">{shortId(job.id)}</p>
          <p className="mt-1 truncate text-xs text-muted-foreground">
            {job.id}
          </p>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      width: "130px",
      cell: (job) => (
        <IngestionStatusBadge
          status={job.status ?? "NOT_STARTED"}
        />
      ),
    },
    {
      id: "documents",
      header: "Documents",
      align: "right",
      width: "140px",
      cell: (job) => (
        <div className="text-right">
          <p className="font-medium tabular-nums">
            {job.completed_files.toLocaleString()} /{" "}
            {job.total_files.toLocaleString()}
          </p>
          <div className="mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{
                width: `${progressPercent(job)}%`,
              }}
            />
          </div>
        </div>
      ),
    },
    {
      id: "failed",
      header: "Failed",
      align: "right",
      width: "90px",
      cell: (job) => (
        <span className="tabular-nums">
          {job.failed_files.toLocaleString()}
        </span>
      ),
    },
    {
      id: "trigger",
      header: "Trigger",
      width: "110px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm">
          {job.trigger_type}
        </span>
      ),
    },
    {
      id: "build-graph",
      header: "Graph",
      width: "90px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm">
          {job.is_build_graph ? "Yes" : "No"}
        </span>
      ),
    },
    {
      id: "scope",
      header: "Scope",
      width: "140px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm">
          {job.scope_type ?? "-"}
        </span>
      ),
    },
    {
      id: "created-at",
      header: "Created",
      width: "170px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm text-muted-foreground">
          {formatDate(job.created_at)}
        </span>
      ),
    },
    {
      id: "started-at",
      header: "Started",
      width: "170px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm text-muted-foreground">
          {formatDate(job.started_at)}
        </span>
      ),
    },
    {
      id: "finished-at",
      header: "Finished",
      width: "170px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm text-muted-foreground">
          {formatDate(job.finished_at)}
        </span>
      ),
    },
    {
      id: "actions",
      header: "",
      align: "right",
      width: "140px",
      cell: (job) => {
        const mutable = job.status !== "COMPLETED";

        return (
          <div className="flex justify-end gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              title="Configure"
              disabled={!mutable}
              onClick={(event) => {
                event.stopPropagation();
                onConfigure(job);
              }}
            >
              <Settings className="size-4" />
            </Button>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              title="Build"
              disabled={!mutable || startMutation.isPending}
              onClick={(event) => {
                event.stopPropagation();
                startMutation.mutate(
                  {
                    jobId: job.id,
                    batchSize: 100,
                  },
                  {
                    onSuccess: () => onStarted?.(job),
                  },
                );
              }}
            >
              <Play className="size-4" />
            </Button>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              title="Details"
              onClick={(event) => {
                event.stopPropagation();
                onRowClick(job);
              }}
            >
              <MoreHorizontal className="size-4" />
            </Button>
          </div>
        );
      },
    },
  ];

  return (
    <div className="px-6 pb-6">
      <DataTable
        columns={columns}
        data={jobs}
        getRowId={(job) => job.id}
        onRowClick={onRowClick}
        loading={loading}
        emptyMessage="No ingestion jobs found."
        className="max-h-[560px] overflow-auto"
      />
    </div>
  );
}

function progressPercent(job: IngestionJob) {
  if (job.total_files <= 0) {
    return 0;
  }

  return Math.min(
    100,
    Math.round(
      (job.completed_files / job.total_files) * 100,
    ),
  );
}

function shortId(id: string) {
  return id.slice(0, 8);
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
