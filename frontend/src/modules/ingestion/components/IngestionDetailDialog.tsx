"use client";

import { BaseModal } from "@/components/shared/modal";
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
  if (!job) {
    return null;
  }

  return (
    <BaseModal
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          onClose();
        }
      }}
      title="Ingestion job"
      description={job.id}
      size="2xl"
      footer={
        <Button
          type="button"
          variant="outline"
          onClick={onClose}
        >
          Close
        </Button>
      }
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <DetailItem
          label="Status"
          value={
            <IngestionStatusBadge
              status={job.status ?? "NOT_STARTED"}
            />
          }
        />
        <DetailItem
          label="Knowledge Space"
          value={job.knowledge_space_id}
        />
        <DetailItem
          label="Trigger"
          value={job.trigger_type}
        />
        <DetailItem
          label="Build Graph"
          value={job.is_build_graph ? "Yes" : "No"}
        />
        <DetailItem
          label="Documents"
          value={`${job.completed_files} / ${job.total_files}`}
        />
        <DetailItem
          label="Failed"
          value={job.failed_files}
        />
        <DetailItem
          label="Scope"
          value={job.scope_type ?? "-"}
        />
        <DetailItem
          label="Created"
          value={formatDate(job.created_at)}
        />
        <DetailItem
          label="Started"
          value={formatDate(job.started_at)}
        />
        <DetailItem
          label="Finished"
          value={formatDate(job.finished_at)}
        />
      </div>
    </BaseModal>
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
      <div className="mt-1 break-words text-sm font-medium">
        {value}
      </div>
    </div>
  );
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
