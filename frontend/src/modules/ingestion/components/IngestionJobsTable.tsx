"use client";

import { MoreHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/shared/data-table";

import { IngestionStatusBadge } from "./IngestionStatusBadge";
import type { IngestionJob } from "../types/ingestion.types";

interface IngestionJobsTableProps {
  jobs: IngestionJob[];
  onRowClick: (job: IngestionJob) => void;
}

export function IngestionJobsTable({
  jobs,
  onRowClick,
}: IngestionJobsTableProps) {
  const columns: DataTableColumn<IngestionJob>[] = [
    {
      id: "name",
      header: "Ingestion",
      width: "260px",
      cell: (job) => (
        <div className="min-w-[220px]">
          <p className="font-medium">{job.name}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {job.id}
          </p>
        </div>
      ),
    },
    {
      id: "source",
      header: "Source",
      width: "190px",
      cell: (job) => (
        <span className="whitespace-nowrap">
          {job.sourceName}
        </span>
      ),
    },
    {
      id: "knowledge-space",
      header: "Knowledge Space",
      width: "180px",
      cell: (job) => (
        <span className="whitespace-nowrap">
          {job.knowledgeSpaceName}
        </span>
      ),
    },
    {
      id: "documents",
      header: "Documents",
      align: "right",
      width: "130px",
      cell: (job) => (
        <div className="text-right">
          <p className="font-medium tabular-nums">
            {job.processedDocumentCount.toLocaleString()} /{" "}
            {job.documentCount.toLocaleString()}
          </p>

          <div className="mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{
                width: `${
                  job.documentCount === 0
                    ? 0
                    : (job.processedDocumentCount /
                        job.documentCount) *
                      100
                }%`,
              }}
            />
          </div>
        </div>
      ),
    },
    {
      id: "stage",
      header: "Current stage",
      width: "150px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm">
          {job.currentStage}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      width: "130px",
      cell: (job) => (
        <IngestionStatusBadge status={job.status} />
      ),
    },
    {
      id: "started-at",
      header: "Started at",
      width: "170px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm text-muted-foreground">
          {job.startedAt}
        </span>
      ),
    },
    {
      id: "finished-at",
      header: "Finished at",
      width: "170px",
      cell: (job) => (
        <span className="whitespace-nowrap text-sm text-muted-foreground">
          {job.finishedAt ?? "—"}
        </span>
      ),
    },
    {
      id: "actions",
      header: "",
      align: "right",
      width: "70px",
      cell: (job) => (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={(event) => {
            event.stopPropagation();
            onRowClick(job);
          }}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      ),
    },
  ];

  return (
    <div className="px-6 pb-6">
      <DataTable
        columns={columns}
        data={jobs}
        getRowId={(job) => job.id}
        onRowClick={onRowClick}
        emptyMessage="No ingestion jobs found."
        className="max-h-[560px] overflow-auto"
      />
    </div>
  );
}