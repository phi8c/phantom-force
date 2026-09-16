"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { IngestionControls } from "./IngestionControls";
import { IngestionConfigModal } from "./ingestion-config-modal/IngestionConfigModal";
import { IngestionCreateDialog } from "./IngestionCreateDialog";
import { IngestionDetailDialog } from "./IngestionDetailDialog";
import { IngestionJobsTable } from "./IngestionJobsTable";
import { IngestionTabs } from "./IngestionTabs";
import { LiveStreamProcessing } from "./live-stream-processing/LiveStreamProcessing";

import { useIngestionFilters } from "../hooks/use-ingestion-filters";
import { useIngestionJobs } from "../hooks/use-ingestion-jobs";
import { useIngestionStore } from "../store/ingestion.store";


interface IngestionPageProps {
  knowledgeSpaceId?: string;
}

export function IngestionPage({
  knowledgeSpaceId,
}: IngestionPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") ?? "overview";
  const {
    filters,
    updateFilters,
    resetFilters,
  } = useIngestionFilters();

  const jobsQuery = useIngestionJobs(
    filters,
    knowledgeSpaceId,
  );
  const jobs = jobsQuery.data?.items ?? [];

  const {
    selectedJobId,
    isCreateDialogOpen,
    isDetailDialogOpen,
    openCreateDialog,
    closeCreateDialog,
    openDetailDialog,
    closeDetailDialog,
  } = useIngestionStore();
  const [configureJobId, setConfigureJobId] =
    useState<string | null>(null);
  const [configOpen, setConfigOpen] = useState(false);
  const [liveJobId, setLiveJobId] = useState<string | null>(
    null,
  );

  const selectedJob = useMemo(
    () =>
      jobs.find((job) => job.id === selectedJobId),
    [jobs, selectedJobId],
  );

  function handleRefresh() {
    void jobsQuery.refetch();
  }

  function openTab(tab: string) {
    const params = new URLSearchParams(
      searchParams.toString(),
    );
    params.set("tab", tab);
    router.push(`?${params.toString()}`);
  }


  return (
    <div className="flex min-h-full flex-col">
      <IngestionTabs />

      {activeTab === "live" ? (
        <LiveStreamProcessing
          jobId={liveJobId}
          onBackToJobs={() => openTab("jobs")}
        />
      ) : (
        <>
          <IngestionControls
            filters={filters}
            onFilterChange={updateFilters}
            onReset={resetFilters}
            onRefresh={handleRefresh}
            onCreate={openCreateDialog}
          />

          <div className="flex h-8 items-center justify-between px-6 py-4">
            <div>
              <h2 className="text-sm font-semibold">
                Ingestion jobs
              </h2>
            </div>
          </div>

          <IngestionJobsTable
            jobs={jobs}
            loading={jobsQuery.isLoading}
            onRowClick={(job) => openDetailDialog(job.id)}
            onConfigure={(job) => {
              setConfigureJobId(job.id);
              setConfigOpen(true);
            }}
            onStarted={(job) => {
              setLiveJobId(job.id);
              void jobsQuery.refetch();
              openTab("live");
            }}
          />
        </>
      )}

      <IngestionCreateDialog
        open={isCreateDialogOpen}
        knowledgeSpaceId={knowledgeSpaceId}
        onClose={closeCreateDialog}
        onCreated={(jobId) => {
          closeCreateDialog();
          setConfigureJobId(jobId);
          setConfigOpen(true);
        }}
      />

      <IngestionConfigModal
        open={configOpen}
        ingestionJobId={configureJobId}
        onOpenChange={(nextOpen) => {
          setConfigOpen(nextOpen);
          if (!nextOpen) {
            setConfigureJobId(null);
          }
        }}
        onSaved={() => void jobsQuery.refetch()}
      />

      <IngestionDetailDialog
        job={selectedJob}
        open={isDetailDialogOpen}
        onClose={closeDetailDialog}
      />
    </div>
  );
}
