"use client";

import { PageTabs } from "@/components/shared/page-tabs";

const ingestionTabs = [
  {
    value: "overview",
    label: "Overview",
  },
  {
    value: "jobs",
    label: "Ingestion Jobs",
  },
  {
    value: "live",
    label: "Live Stream Processing",
  },
  {
    value: "schedules",
    label: "Schedules",
  },
  {
    value: "history",
    label: "History",
  },
];

export function IngestionTabs() {
  return (
    <PageTabs
      tabs={ingestionTabs}
      defaultValue="overview"
    />
  );
}
