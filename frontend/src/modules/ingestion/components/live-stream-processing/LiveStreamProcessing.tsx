"use client";

import {
  Activity,
  ArrowLeft,
  CheckCircle2,
  CircleDashed,
  Files,
  Radio,
  RefreshCw,
  TriangleAlert,
} from "lucide-react";

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
      <div className="grid min-h-[460px] place-items-center bg-[var(--app-canvas)] px-6 text-[var(--app-ink)] [font-family:var(--app-font)]">
        <div className="text-center">
          <CircleDashed className="mx-auto size-10 opacity-60" />
          <h2 className="mt-3 text-base font-semibold">
            No live ingestion selected
          </h2>
          <button
            type="button"
            className="mt-4 cursor-pointer rounded-md border border-[var(--app-outline)] bg-white px-4 py-2 text-sm font-medium hover:bg-[var(--app-highlight)]"
            onClick={onBackToJobs}
          >
            Open jobs
          </button>
        </div>
      </div>
    );
  }

  const job = snapshot?.job;

  return (
    <div className="min-h-full bg-[var(--app-canvas)] px-4 py-6 text-[var(--app-ink)] [font-family:var(--app-font)] sm:px-6">
      <section>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "inline-flex size-2.5 rounded-full",
                  connected
                    ? "bg-emerald-500"
                    : "bg-[var(--app-outline)]",
                )}
              />
              <h2 className="text-lg font-semibold">
                Live Stream Processing
              </h2>
            </div>
            <p className="mt-1 break-all text-xs opacity-70">
              {jobId}
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-[var(--app-outline)] bg-white px-4 py-1.5 text-sm font-medium hover:bg-[var(--app-highlight)]"
              onClick={() => void refetch()}
            >
              <RefreshCw className="size-4" aria-hidden="true" />
              Refresh
            </button>
            <button
              type="button"
              className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-[var(--app-outline)] bg-white px-4 py-1.5 text-sm font-medium hover:bg-[var(--app-highlight)]"
              onClick={onBackToJobs}
            >
              <ArrowLeft className="size-4" aria-hidden="true" />
              Jobs
            </button>
          </div>
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-700" role="alert">
            Unable to load orchestration snapshot.
          </p>
        )}

        <div className="mt-5 grid gap-4 border-b border-[var(--app-outline)] pb-6 sm:grid-cols-2 xl:grid-cols-4">
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

      <section className="grid gap-6 pt-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
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

        <div className="overflow-hidden rounded-lg border border-[var(--app-outline)] bg-[var(--app-surface)]">
          <div className="flex items-center gap-2 border-b border-[var(--app-outline)] px-4 py-3">
            <Radio className="size-4" />
            <span className="text-sm font-medium">
              Event stream
            </span>
          </div>
          <div className="max-h-64 overflow-auto p-2">
            {events.length === 0 ? (
              <p className="px-2 py-8 text-center text-sm opacity-70">
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
    <div className="flex min-h-28 flex-col gap-3 rounded-lg border border-[var(--app-outline)] bg-[var(--app-surface)] p-4">
      <div className="flex items-center gap-2 text-sm font-medium opacity-90">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-3xl font-bold tabular-nums">
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
    <div className="flex min-w-0 flex-col gap-3 rounded-lg border border-[var(--app-outline)] bg-[var(--app-surface)] p-3">
      <div className="flex min-h-5 items-center justify-between gap-2">
        <h3 className="min-w-0 truncate text-sm font-semibold" title={stage}>
          {stage}
        </h3>
        <span className="grid size-6 shrink-0 place-items-center rounded-full bg-[var(--app-highlight)] text-xs tabular-nums" aria-label={`${total} items`}>
          {total}
        </span>
      </div>
      <div className="grid grid-cols-3 rounded-md bg-[var(--app-canvas)] px-1 py-1 text-center text-xs">
        <StagePill label="Run" value={processing} />
        <StagePill label="Done" value={completed} />
        <StagePill label="Fail" value={failed} />
      </div>
      <div className="flex h-36 flex-col gap-2 overflow-auto rounded-md bg-[var(--app-canvas)] p-2">
        {events.slice(-5).map((event) => (
          <div
            key={event.sequence_no}
            className={cn(
              "rounded-md border px-2 py-2 text-xs transition-colors",
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
              <span className="truncate" title={event.status ?? event.event_type}>
                {event.status ?? event.event_type}
              </span>
            </div>
          </div>
        ))}

        {events.length === 0 && (
          <div className="grid flex-1 place-items-center text-sm opacity-70">
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
    <div className="flex flex-col px-1 py-0.5">
      <div className="font-semibold tabular-nums">{value}</div>
      <div className="opacity-75">{label}</div>
    </div>
  );
}

function EventRow({
  event,
}: {
  event: OrchestrationEvent;
}) {
  return (
    <div className="grid gap-1 rounded-md px-2 py-2 text-xs hover:bg-[var(--app-canvas)] md:grid-cols-[80px_150px_1fr_110px]">
      <span className="font-medium tabular-nums">
        #{event.sequence_no}
      </span>
      <span>{event.event_type}</span>
      <span className="truncate opacity-75" title={event.document_id ?? event.ingestion_batch_id ?? ""}>
        {event.document_id ?? event.ingestion_batch_id ?? "-"}
      </span>
      <span className="opacity-75">
        {event.stage ?? "-"}
      </span>
    </div>
  );
}

function shortId(id: string) {
  return id ? id.slice(0, 8) : "-";
}
