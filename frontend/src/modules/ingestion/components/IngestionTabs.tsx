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