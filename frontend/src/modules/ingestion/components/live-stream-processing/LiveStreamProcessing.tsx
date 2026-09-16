"use client";

import {
  Activity,
  CheckCircle2,
  CircleDashed,
  Files,
  Radio,
  TriangleAlert,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useOrchestrationLive } from "../../hooks/use-orchestration-live";
import type { OrchestrationEvent } from "../../types/orchestration.types";

interface LiveStreamProcessingProps {
  jobId: string | null;
  onBackToJobs: () => void;
}

const stages = [
  "DISCOVERY",
  "DOWNLOAD",
  "EXTRACTION",
  "CHUNKING",
  "EMBEDDING",
  "CLASSIFICATION",
];

export function LiveStreamProcessing({
  jobId,
  onBackToJobs,
}: LiveStreamProcessingProps) {
  const {
    snapshot,
    events,
    connected,
    loading,
    error,
    refetch,
  } = useOrchestrationLive(jobId);

  if (!jobId) {
    return (
      <div className="grid min-h-[460px] place-items-center px-6">
        <div className="text-center">
          <CircleDashed className="mx-auto size-10 text-muted-foreground" />
          <h2 className="mt-3 text-base font-semibold">
            No live ingestion selected
          </h2>
          <Button
            type="button"
            variant="outline"
            className="mt-4"
            onClick={onBackToJobs}
          >
            Open jobs
          </Button>
        </div>
      </div>
    );
  }

  const job = snapshot?.job;

  return (
    <div className="flex min-h-full flex-col">
      <section className="border-b px-6 py-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "inline-flex size-2.5 rounded-full",
                  connected
                    ? "bg-emerald-500"
                    : "bg-muted-foreground",
                )}
              />
              <h2 className="text-sm font-semibold">
                Live Stream Processing
              </h2>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {jobId}
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void refetch()}
            >
              Refresh
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onBackToJobs}
            >
              Jobs
            </Button>
          </div>
        </div>

        {error && (
          <p className="mt-3 text-sm text-destructive">
            Unable to load orchestration snapshot.
          </p>
        )}

        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Metric
            icon={<Files className="size-4" />}
            label="Files"
            value={
              job
                ? `${job.completed_files}/${job.total_files}`
                : loading
                  ? "Loading"
                  : "0/0"
            }
          />
          <Metric
            icon={<Activity className="size-4" />}
            label="Processing batches"
            value={job?.processing_batches ?? 0}
          />
          <Metric
            icon={<CheckCircle2 className="size-4" />}
            label="Completed batches"
            value={job?.completed_batches ?? 0}
          />
          <Metric
            icon={<TriangleAlert className="size-4" />}
            label="Failed"
            value={job?.failed_files ?? 0}
          />
        </div>
      </section>

      <section className="grid gap-5 px-6 py-5">
        <div className="grid gap-3 xl:grid-cols-6">
          {stages.map((stage) => (
            <StageColumn
              key={stage}
              stage={stage}
              counts={
                snapshot?.stages?.[stage.toLowerCase()] ?? {}
              }
              events={events.filter(
                (event) => event.stage === stage,
              )}
            />
          ))}
        </div>

        <div className="rounded-lg border">
          <div className="flex items-center gap-2 border-b px-3 py-2">
            <Radio className="size-4 text-emerald-600" />
            <span className="text-sm font-medium">
              Event stream
            </span>
          </div>
          <div className="max-h-64 overflow-auto p-2">
            {events.length === 0 ? (
              <p className="px-2 py-8 text-center text-sm text-muted-foreground">
                Waiting for orchestration events.
              </p>
            ) : (
              [...events]
                .reverse()
                .slice(0, 40)
                .map((event) => (
                  <EventRow
                    key={event.sequence_no}
                    event={event}
                  />
                ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-card px-3 py-3">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums">
        {value}
      </div>
    </div>
  );
}

function StageColumn({
  stage,
  counts,
  events,
}: {
  stage: string;
  counts: Record<string, number>;
  events: OrchestrationEvent[];
}) {
  const processing = counts.processing ?? 0;
  const completed = counts.completed ?? 0;
  const failed = counts.failed ?? 0;
  const ready = counts.ready ?? 0;
  const total = processing + completed + failed + ready;

  return (
    <div className="min-h-[300px] rounded-lg border bg-card">
      <div className="border-b px-3 py-3">
        <div className="flex items-center justify-between gap-2">
          <h3 className="truncate text-sm font-semibold">
            {stage}
          </h3>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs tabular-nums text-muted-foreground">
            {total}
          </span>
        </div>
        <div className="mt-3 grid grid-cols-3 gap-1 text-center text-[11px]">
          <StagePill label="Run" value={processing} />
          <StagePill label="Done" value={completed} />
          <StagePill label="Fail" value={failed} />
        </div>
      </div>

      <div className="space-y-2 p-2">
        {events.slice(-8).map((event) => (
          <div
            key={event.sequence_no}
            className={cn(
              "rounded-md border px-2 py-2 text-xs shadow-sm transition-colors",
              event.status === "COMPLETED" &&
                "border-emerald-200 bg-emerald-50 text-emerald-900",
              event.status === "FAILED" &&
                "border-red-200 bg-red-50 text-red-900",
              event.status === "PROCESSING" &&
                "border-sky-200 bg-sky-50 text-sky-900",
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">
                {event.document_id
                  ? shortId(event.document_id)
                  : shortId(event.ingestion_batch_id ?? "")}
              </span>
              <span>{event.status ?? event.event_type}</span>
            </div>
          </div>
        ))}

        {events.length === 0 && (
          <div className="rounded-md border border-dashed px-2 py-8 text-center text-xs text-muted-foreground">
            Idle
          </div>
        )}
      </div>
    </div>
  );
}

function StagePill({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-md bg-muted px-1.5 py-1">
      <div className="font-semibold tabular-nums">{value}</div>
      <div className="text-muted-foreground">{label}</div>
    </div>
  );
}

function EventRow({
  event,
}: {
  event: OrchestrationEvent;
}) {
  return (
    <div className="grid gap-1 rounded-md px-2 py-2 text-xs hover:bg-muted/50 md:grid-cols-[80px_150px_1fr_110px]">
      <span className="font-medium tabular-nums">
        #{event.sequence_no}
      </span>
      <span>{event.event_type}</span>
      <span className="truncate text-muted-foreground">
        {event.document_id ?? event.ingestion_batch_id ?? "-"}
      </span>
      <span className="text-muted-foreground">
        {event.stage ?? "-"}
      </span>
    </div>
  );
}

function shortId(id: string) {
  return id ? id.slice(0, 8) : "-";
}
