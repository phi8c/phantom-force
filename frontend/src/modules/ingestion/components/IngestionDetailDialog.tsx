"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";

import { IngestionStatusBadge } from "./IngestionStatusBadge";
import type { IngestionJob } from "../types/ingestion.types";

interface IngestionDetailDialogProps {
  job?: IngestionJob;
  open: boolean;
  onClose: () => void;
}

export function IngestionDetailDialog({
  job,
  open,
  onClose,
}: IngestionDetailDialogProps) {
  if (!open || !job) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-2xl rounded-xl border bg-background shadow-xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">
              {job.name}
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              Ingestion job details
            </p>
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
          >
            <X className="size-4" />
          </Button>
        </div>

        <div className="grid gap-5 px-6 py-5 sm:grid-cols-2">
          <DetailItem label="Job ID" value={job.id} />
          <DetailItem
            label="Status"
            value={<IngestionStatusBadge status={job.status} />}
          />
          <DetailItem
            label="Source"
            value={job.sourceName}
          />
          <DetailItem
            label="Knowledge Space"
            value={job.knowledgeSpaceName}
          />
          <DetailItem
            label="Current stage"
            value={job.currentStage}
          />
          <DetailItem
            label="Documents"
            value={`${job.processedDocumentCount} / ${job.documentCount}`}
          />
          <DetailItem
            label="Started at"
            value={job.startedAt}
          />
          <DetailItem
            label="Finished at"
            value={job.finishedAt ?? "—"}
          />

          {job.errorMessage && (
            <div className="sm:col-span-2">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Error
              </p>

              <p className="mt-1 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                {job.errorMessage}
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end border-t px-6 py-4">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}

interface DetailItemProps {
  label: string;
  value: React.ReactNode;
}

function DetailItem({ label, value }: DetailItemProps) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>

      <div className="mt-1 text-sm font-medium">
        {value}
      </div>
    </div>
  );
}