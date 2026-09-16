"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  createOrchestrationEventSource,
  getOrchestrationSnapshot,
} from "../api/orchestration.api";
import type {
  OrchestrationEvent,
  OrchestrationSnapshot,
} from "../types/orchestration.types";
import { ingestionQueryKeys } from "./use-ingestion-config";

export function useOrchestrationLive(jobId: string | null) {
  const [events, setEvents] = useState<OrchestrationEvent[]>(
    [],
  );
  const [connected, setConnected] = useState(false);

  const snapshotQuery = useQuery({
    queryKey: [
      ...ingestionQueryKeys.all,
      "orchestration",
      jobId ?? "",
    ],
    queryFn: () => getOrchestrationSnapshot(jobId ?? ""),
    enabled: Boolean(jobId),
    refetchInterval: connected ? false : 3000,
  });

  useEffect(() => {
    setEvents([]);

    if (!jobId) {
      setConnected(false);
      return;
    }

    const source = createOrchestrationEventSource(jobId);

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    const eventTypes = [
      "BATCH_CREATED",
      "DOCUMENT_STAGE_READY",
      "DOCUMENT_STAGE_PROCESSING",
      "DOCUMENT_STAGE_COMPLETED",
      "DOCUMENT_STAGE_FAILED",
      "DOCUMENT_STAGE_SKIPPED",
      "BATCH_COMPLETED",
    ];

    for (const type of eventTypes) {
      source.addEventListener(type, (event) => {
        appendEvent((event as MessageEvent).data);
      });
    }

    function appendEvent(data: string) {
      try {
        const parsed = JSON.parse(data) as OrchestrationEvent;
        setEvents((current) =>
          dedupeEvents([...current, parsed]).slice(-120),
        );
      } catch {
        // Ignore malformed SSE messages.
      }
    }

    return () => {
      source.close();
      setConnected(false);
    };
  }, [jobId]);

  const derivedSnapshot = useMemo(
    () => mergeSnapshotWithEvents(snapshotQuery.data, events),
    [events, snapshotQuery.data],
  );

  return {
    snapshot: derivedSnapshot,
    events,
    connected,
    loading: snapshotQuery.isLoading,
    error: snapshotQuery.error,
    refetch: snapshotQuery.refetch,
  };
}

function dedupeEvents(events: OrchestrationEvent[]) {
  const bySequence = new Map<number, OrchestrationEvent>();

  for (const event of events) {
    bySequence.set(event.sequence_no, event);
  }

  return [...bySequence.values()].sort(
    (left, right) => left.sequence_no - right.sequence_no,
  );
}

function mergeSnapshotWithEvents(
  snapshot: OrchestrationSnapshot | undefined,
  events: OrchestrationEvent[],
) {
  if (!snapshot) {
    return snapshot;
  }

  const stages = structuredClone(snapshot.stages ?? {});

  for (const event of events) {
    if (!event.stage || !event.status) {
      continue;
    }

    const stageKey = event.stage.toLowerCase();
    const statusKey = event.status.toLowerCase();

    stages[stageKey] = {
      ...(stages[stageKey] ?? {}),
      [statusKey]:
        (stages[stageKey]?.[statusKey] ?? 0) + 1,
    };
  }

  return {
    ...snapshot,
    stages,
  };
}
